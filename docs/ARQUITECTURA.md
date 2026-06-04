# 🏗️ Arquitectura del sistema

Visión general del proyecto: una **API REST (FastAPI)** que expone bots de IA sobre
documentos (RAG), un servicio de **voz** y un módulo de **consultas a datos**
(NL → SQL / API REST). Este documento explica cómo encajan las piezas y cómo se integró
la voz, para que el sistema sea entendible y escalable.

> Para **usar/integrar** el módulo de consultas, ver [API_CONSULTAS.md](API_CONSULTAS.md).
> Para la API completa de todos los bots, ver [API_DOCUMENTATION.md](API_DOCUMENTATION.md).
> Para despliegue, ver [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 🗺️ Vista general

```
                          FastAPI (app.main:app)
                                   │
                 ┌─────────────────┼───────────────────────────┐
                 ▼                 ▼                 ▼           ▼
          /bot-simple       /bot-avanzado          /voz     /consultas
          (RAG Chroma+      (RAG Chroma+         (STT+RAG+   (NL→SQL / API REST,
           Ollama)           LLM configurable)     TTS)        solo lectura)
                 │                 │                 │           │
                 └──────── ChromaDB / Paperless ─────┘     MySQL RO / APIs REST
                                   │
                          LLM (LLM_PROVIDER): ollama | openai | opencode
```

Capas (patrón consistente en todo el repo):

```
app/
├── main.py                 # App FastAPI + middleware + lifespan
├── api/v1/
│   ├── router.py           # Agrega los routers v1
│   └── endpoints/          # Rutas HTTP (bot_simple, bot_avanzado, voz, consultas)
├── services/               # Lógica de negocio (no sabe de HTTP)
│   ├── rag_simple.py / rag_avanzado.py
│   ├── voz.py              # Orquestación de voz para el RAG
│   └── consultas/          # Módulo de consultas a datos (ver abajo)
├── clients/                # Integraciones externas (paperless, stt, tts, mysql)
├── schemas/                # Modelos Pydantic (request/response)
└── core/                   # config (settings) y logging
```

**Principio:** el endpoint valida y traduce HTTP ↔ Pydantic; el *service* contiene la
lógica; el *client* habla con sistemas externos. `core/config.py` es la única fuente de
configuración (variables de entorno).

---

## 🔧 Stack

- **API:** FastAPI + Uvicorn/Gunicorn.
- **RAG:** LangChain + ChromaDB (embeddings locales con Ollama o OpenAI según `LOCALIA`).
- **LLM de chat/generación:** conmutable con `LLM_PROVIDER` (`ollama` | `openai` | `opencode`).
- **Datos (consultas):** SQLAlchemy + PyMySQL (MySQL/MariaDB), `sqlglot` (validación SQL),
  `requests` (REST), `PyYAML` (catálogo de reglas).
- **Voz:** faster-whisper (STT) + Piper (TTS) en local, u OpenAI como alternativa.

---

## 🎙️ Cómo se integró el servicio de voz

La voz **no reimplementa** la lógica de negocio: es una capa que envuelve a un servicio
existente con **STT → (servicio) → TTS**.

```
audio ──► STT (clients/stt.py) ──► texto ──► [RAG | Consultas] ──► texto ──► TTS (clients/tts.py) ──► audio
```

- **`clients/stt.py`** — transcribe audio a texto. Proveedor conmutable (`STT_PROVIDER`):
  `local` (faster-whisper + ffmpeg) u `openai`. Carga perezosa del modelo Whisper.
- **`clients/tts.py`** — sintetiza texto a WAV. Proveedor conmutable (`TTS_PROVIDER`):
  `local` (Piper) u `openai`.
- **`services/voz.py`** — voz sobre el **RAG** (`/api/v1/voz`): transcribe y reenvía al bot
  configurado por `VOICE_BACKEND` (simple/avanzado).
- **`services/consultas/voz.py`** — voz sobre el **módulo de consultas**
  (`/api/v1/consultas/voz`): transcribe, llama al orquestador de consultas y devuelve el
  objeto estructurado + un **resumen hablado corto** (no dicta tablas enteras).

**Por qué así:** reutilizar los mismos clientes STT/TTS evita duplicar lógica y mantiene la
configuración de voz centralizada. Añadir voz a un nuevo servicio = transcribir la
entrada, llamar al service y (opcional) sintetizar una respuesta breve.

Requisitos de voz: `VOICE_ENABLED=true`; en local, `ffmpeg` + modelos descargados
(`scripts/descargar_modelos_voz.py`). Guía de cliente: [INTEGRACION_VOZ_CLIENTE.md](INTEGRACION_VOZ_CLIENTE.md).

---

## 🗂️ Módulo de consultas a datos

Ubicación: `app/services/consultas/`. Cada archivo tiene una responsabilidad única:

| Archivo | Responsabilidad |
|---------|-----------------|
| `catalogo.py` | Carga `rules.yaml`; matcher por `keys`; búsqueda por nombre (`objetivo`); expansión de relaciones (FK) |
| `llm.py` | Factory del LLM de chat (reusa `LLM_PROVIDER`) |
| `generador.py` | NL → SQL (MySQL) / NL → intent REST; decide `texto`/`tabla`/`grafico`; recibe los JOIN |
| `seguridad_sql.py` | Validación de solo lectura (sqlglot): allowlist, `LIMIT`, bloqueo de DML/DDL/peligros |
| `ejecutor_sql.py` | Ejecuta el `SELECT` (tope de filas, timeout) |
| `ejecutor_rest.py` | Cliente `GET` con anti-SSRF y aplanado de JSON a filas |
| `formateador.py` | Arma el objeto estructurado; construye gráficos (agregación `conteo`/`suma`); personaliza el texto |
| `orquestador.py` | Une todo el flujo y expone `procesar_consulta(...)` y `estado()` |
| `voz.py` | Variante por voz (STT → orquestador → TTS) |

`clients/mysql.py` — factory de engines SQLAlchemy por origen (cache), con sesión de solo
lectura y timeout (compatible MySQL y MariaDB).

### Flujo de una consulta

```
procesar_consulta(consulta, origen, formato?, usuario?, objetivo?)
  │
  ├─ catalogo: origen válido? → candidatos (objetivo directo o matcher por keys)
  ├─ SQL:  expandir_relaciones (FK) → generador.generar_sql → seguridad_sql → ejecutor_sql
  ├─ REST: generador.generar_intent_rest → ejecutor_rest
  └─ formateador.construir_respuesta → ConsultaResponse {texto|tabla|grafico, meta}
```

### Decisiones de diseño

- **Catálogo de reglas (`rules.yaml`)** como allowlist: limita qué se puede consultar,
  reduce tokens (solo se envía el esquema relevante) y guía al modelo. Sin secretos: los
  DSN/URLs se referencian por nombre de variable de entorno.
- **Solo lectura en capas:** usuario de BD read-only + validación de SQL + sesión read-only.
- **Salida estructurada** en vez de HTML: el frontend decide cómo pintar (tabla, Chart.js…).
- **`objetivo` y `relaciones`** para consultas de módulos específicos: fijar la entidad y
  declarar JOINs reduce ambigüedad y errores en relaciones foráneas.

### Fases

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Orígenes REST + MySQL read-only, catálogo, NL→SQL/intent, salida `texto`/`tabla`, seguridad en capas | ✅ |
| 2 | `grafico` (Chart.js) con agregación en servidor (REST) o `GROUP BY` (SQL) | ✅ |
| — | Voz, personalización (`usuario`), consulta dirigida (`objetivo`) + relaciones FK | ✅ |

---

## ⚙️ Configuración (resumen)

Toda la configuración vive en `.env` (leída por `app/core/config.py`). Variables clave por
área:

- **IA/RAG:** `LOCALIA`, `LLM_PROVIDER`, `OLLAMA_*`, `OPENAI_*`, `OPENCODE_*`, `CHROMA_*`.
- **Voz:** `VOICE_ENABLED`, `VOICE_BACKEND`, `STT_PROVIDER`, `TTS_PROVIDER`, `WHISPER_*`, `PIPER_*`.
- **Consultas:** `CONSULTAS_ENABLED`, `RULES_PATH`, `CONSULTAS_MAX_FILAS`,
  `CONSULTAS_SQL_TIMEOUT`, `CONSULTAS_REST_TIMEOUT`, y los DSN de cada origen (read-only).

Ver `.env.example` para la lista completa y comentada.
