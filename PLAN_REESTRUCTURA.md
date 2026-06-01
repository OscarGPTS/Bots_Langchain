# 🏗️ Plan de Reestructuración — API RAG (FastAPI + LangChain)

> **Estado:** Propuesta para revisión. **No** se ha modificado código todavía.
> **Decisiones tomadas:**
> - Alcance: plan detallado primero (este documento), ejecución posterior por fases.
> - Autenticación: **solo Cloudflare Zero Trust** (sin auth propia de la app). Solo se blinda `/reindexar`.
> **Fecha:** 2026-06-01

---

## 1. Premisa corregida (importante)

La carpeta `bots/` **NO es código de prueba**. Es el **núcleo de negocio** del que depende la API:

- [api/dependencies.py](api/dependencies.py) importa `BotDocumentos` y `BotDocumentosAvanzado` directamente.
- Mover `bots/` a `tests/` **rompería producción**.

Lo que **sí** es desechable/prueba está en `scripts/` (`test_*.py`, `prueba_*.py`, `probar_*.py`). Esa es la carpeta que migra a `tests/`.

**Conclusión:** `bots/` no se "muda a tests", se **promueve a capa de servicios/dominio** de la API.

---

## 2. Estructura objetivo

```
proyecto/
├── pyproject.toml              # empaquetado + deps + config de herramientas
├── app/                        # (renombre de "api") paquete de aplicación
│   ├── main.py                 # crear app, montar routers y middlewares
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings) — ÚNICA fuente de config
│   │   ├── logging.py          # logging estructurado (reemplaza print)
│   │   └── security.py         # dependencia para proteger /reindexar
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # agrega routers de v1
│   │       └── endpoints/
│   │           ├── bot_simple.py
│   │           └── bot_avanzado.py
│   ├── schemas/                # (renombre de "models/") Pydantic
│   │   └── __init__.py
│   ├── services/               # ← LÓGICA de los "bots" (dominio RAG)
│   │   ├── rag_simple.py
│   │   └── rag_avanzado.py
│   ├── clients/                # integraciones externas aisladas
│   │   ├── paperless.py        # cliente HTTP Paperless
│   │   ├── llm.py              # factory Ollama/OpenAI según LOCALIA
│   │   └── vector_store.py     # ChromaDB
│   └── dependencies.py         # singletons / inyección de dependencias
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/                    # SOLO utilidades operativas reales
├── data/  ·  chroma_db/  ·  .env  ·  requirements.txt
```

---

## 3. Mapeo archivo-por-archivo

### 3.1. `bots/` → `app/services/` + `app/clients/`

| Origen | Destino | Acción |
|---|---|---|
| [bots/bot_documentos.py](bots/bot_documentos.py) | `app/services/rag_simple.py` | Mover lógica RAG. Extraer la parte HTTP de Paperless → `app/clients/paperless.py`. Extraer init de ChromaDB → `app/clients/vector_store.py`. Eliminar `main()` (CLI) y la presentación con emojis. |
| [bots/bot_documentos_avanzado.py](bots/bot_documentos_avanzado.py) | `app/services/rag_avanzado.py` | Igual que arriba. Extraer factory de LLM (Ollama/OpenAI según `LOCALIA`) → `app/clients/llm.py`. |
| [bots/bot_rh.py](bots/bot_rh.py) | `app/services/rh.py` *o* `tools/` | **Decisión pendiente** (ver §7). Si no se expondrá en la API, va a `tools/` o `tests/`. |
| [bots/bot_general.py](bots/bot_general.py) | `app/services/general.py` *o* `tools/` | Igual que `bot_rh.py`. |

**Extracciones nuevas (eliminan duplicación y acoplamiento):**

- `app/clients/paperless.py`: centraliza `GET /api/documents`, `obtener_contenido`, construcción de URLs (`download/preview/thumb`). Hoy el método `_build_document_urls` está **duplicado** en [api/routes/bot_simple.py:22](api/routes/bot_simple.py#L22) y [api/routes/bot_avanzado.py:24](api/routes/bot_avanzado.py#L24).
- `app/clients/llm.py`: única lógica para elegir Ollama vs OpenAI.
- `app/clients/vector_store.py`: init y acceso a ChromaDB (colecciones `docs_simple` / avanzada).

### 3.2. `api/` → `app/`

| Origen | Destino | Acción |
|---|---|---|
| [api/main.py](api/main.py) | `app/main.py` | Adelgazar: solo creación de app, CORS, logging middleware, montaje de routers. Mover config inline a `app/core/`. |
| [api/main_docs.py](api/main_docs.py) | — | **Eliminar.** Es un duplicado casi idéntico de `main.py`; `/docs` ya se sirve desde la app principal. |
| [api/dependencies.py](api/dependencies.py) | `app/dependencies.py` | Quitar el hack `sys.path.insert(...)` (lo resuelve `pyproject.toml`). Mantener singletons. |
| [api/models/schemas.py](api/models/schemas.py) | `app/schemas/__init__.py` (o dividido) | Mover tal cual. Opcional: dividir en `requests.py`/`responses.py`. |
| [api/routes/bot_simple.py](api/routes/bot_simple.py) | `app/api/v1/endpoints/bot_simple.py` | Endpoints solo orquestan: validar → llamar servicio → responder. Sin lógica de negocio ni formateo con emojis. |
| [api/routes/bot_avanzado.py](api/routes/bot_avanzado.py) | `app/api/v1/endpoints/bot_avanzado.py` | Igual. Proteger `/reindexar` (ver §5). |
| [api/routes/__init__.py](api/routes/__init__.py) | `app/api/v1/router.py` | Reorganizar como agregador de routers v1. |

### 3.3. `scripts/` → `tests/` (lo que es prueba)

| Archivo | Destino | Tipo |
|---|---|---|
| `scripts/test_api_cliente.py` | `tests/integration/` | Test E2E de endpoints |
| `scripts/test_api_imports.py` | `tests/unit/` | Smoke test de imports |
| `scripts/test_casos_reales.py` | `tests/integration/` | Test |
| `scripts/test_problema.py` | `tests/integration/` | Test |
| `scripts/test_realista.py` | `tests/integration/` | Test |
| `scripts/test_simple.py` | `tests/unit/` | Test |
| `scripts/prueba_bot_simple.py` | `tests/integration/` | Test |
| `scripts/prueba_simple_bot_avanzado.py` | `tests/integration/` | Test |
| `scripts/probar_bot_documentos.py` | `tests/integration/` | Test |
| `scripts/probar_bot_avanzado.py` | `tests/integration/` | Test |
| `scripts/probar_api_rh.py` | `tests/integration/` | Test |
| `scripts/validacion_final.py` | `tests/integration/` | Validación |

> Nota: hoy son scripts ejecutables con `print`/`input`. Al migrar conviene adaptarlos a funciones `test_*()` para `pytest` (se puede hacer gradualmente; en Fase 0 basta con moverlos).

### 3.4. `scripts/` que se quedan (operativos reales)

| Archivo | Acción |
|---|---|
| `scripts/generar_token_paperless.py` | Mantener en `scripts/` |
| `scripts/inspeccionar_chromadb.py` | Mantener (diagnóstico) |
| `scripts/debug_busqueda.py` | Mantener (diagnóstico) |
| `scripts/instalar_bot_avanzado.py` | Revisar; probablemente obsoleto con `pyproject.toml` |
| `scripts/crear_db_ejemplo.py` | Mantener o convertir en fixture de tests |
| `scripts/indexar_docs_simple.py` | **Renombrar** a `scripts/indexar_docs.py` y volverlo el mecanismo oficial de indexación (ver §6) |
| `scripts/iniciar_api.py` | Opcional eliminar; reemplazado por `uvicorn app.main:app --reload` |
| `scripts/probar_paperless.py` | Mover a `tests/integration/` o dejar como diagnóstico en `scripts/` |
| [utils/verificar_ollama.py](utils/verificar_ollama.py) | Mover a `scripts/` (diagnóstico). Eliminar carpeta `utils/`. |

---

## 4. Refactors transversales (calidad)

1. **Configuración central** — `app/core/config.py` con `pydantic-settings`:
   - Reemplaza los `load_dotenv()` + `os.getenv(...)` dispersos en cada módulo.
   - Valida tipos y obligatoriedad al arranque (falla rápido si falta `PAPERLESS_TOKEN`).
   - Inyectable y mockeable en tests.

2. **Logging en vez de `print`** — `app/core/logging.py`:
   - Hoy hay `print()` por todo el código (bots y rutas). Riesgo: el token de Paperless puede acabar en journald.
   - Logger con niveles; nunca loguear secretos.

3. **Endpoints devuelven datos, no strings con emojis** — La lógica de presentación (`🤖 ─── 📚 Documentos consultados`) sale del backend; la API responde estructurado y el frontend formatea. (Cambio de contrato: ver §8 sobre compatibilidad.)

4. **Empaquetado** — `pyproject.toml` elimina el `sys.path.insert(...)` de [api/dependencies.py:5](api/dependencies.py#L5). Instalación con `pip install -e .`.

---

## 5. Seguridad (sin auth propia; solo Cloudflare + blindaje de `/reindexar`)

| # | Hallazgo | Corrección propuesta |
|---|---|---|
| 1 | `allow_origins=["*"]` con `allow_credentials=True` ([api/main.py:83](api/main.py#L83)) | Definir `CORS_ORIGINS` en config (lista explícita). Si se necesita `*`, poner `allow_credentials=False`. |
| 2 | Handler global expone `str(exc)` ([api/main.py:182](api/main.py#L182)) | Responder mensaje genérico al cliente; el detalle va solo al log. |
| 3 | Token de Paperless en URLs JSON ([bot_simple.py:34](api/routes/bot_simple.py#L34)) | Documentar el riesgo; opcionalmente, endpoint proxy futuro. Sin cambio funcional ahora. |
| 4 | `POST /reindexar` sin protección | **Blindar:** requerir un `ADMIN_TOKEN` (header) leído de `.env`, validado por dependencia `app/core/security.py`. Es el único endpoint protegido. |
| 5 | `print` puede filtrar secretos | Resuelto por logging (§4.2). |

> Se descarta API Key global y JWT por decisión del usuario. La seguridad perimetral sigue siendo Cloudflare Zero Trust.

---

## 6. Indexación fuera del arranque

**Problema actual:** el `__init__` de los bots descarga e indexa todos los documentos de forma **bloqueante y síncrona** ([bots/bot_documentos.py:25-35](bots/bot_documentos.py#L25-L35)). Con Gunicorn de 4 workers → 4 procesos indexando contra la misma ChromaDB (riesgo de carrera/corrupción) y arranque lento.

**Propuesta:**
- El arranque (`lifespan`) **solo conecta** a ChromaDB/Paperless/LLM; no indexa.
- La indexación pasa a `scripts/indexar_docs.py` (cron/manual) y al endpoint `/reindexar` (ya protegido).
- Health check reporta si hay índice disponible.

---

## 7. Decisiones pendientes (para confirmar antes de Fase 2)

1. **`bot_rh.py` y `bot_general.py`:** ¿se expondrán como endpoints de la API, o siguen siendo herramientas manuales? Determina si van a `app/services/` o a `tools/`.
2. **Contrato de respuesta:** ¿migramos las respuestas de string-con-emojis a JSON estructurado (rompe clientes actuales), o mantenemos compatibilidad con un campo `respuesta` de texto? (ver §8).
3. **`requirements.txt` vs `pyproject.toml`:** ¿migrar dependencias a `pyproject.toml` o mantener ambos?

---

## 8. Impacto en producción y compatibilidad

El despliegue usa `gunicorn api.main:app` ([DEPLOYMENT.md](DEPLOYMENT.md)). El renombre `api/` → `app/` **obliga** a actualizar en el servidor:

- `/etc/systemd/system/bots.service` → `gunicorn app.main:app`
- `PYTHONPATH` y rutas en el `.service`
- Referencias en [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md), [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

**Rutas de la API (`/api/v1/bot-simple`, etc.) NO cambian** → los clientes externos no se ven afectados, *salvo* que cambiemos el contrato de respuesta (§7.2).

---

## 9. Fases de ejecución

| Fase | Contenido | Impacto runtime | Reversible |
|---|---|---|---|
| **0** | `pyproject.toml`; mover `test_*`/`prueba_*`/`probar_*` a `tests/`; configurar `pytest` | Ninguno | Sí |
| **1** | `app/core/config.py`; logging; fixes seguridad #1, #2; blindar `/reindexar` (#4) | Bajo (sin mover carpetas) | Sí |
| **2** | Extraer `clients/`; mover bots a `services/`; adelgazar endpoints | Medio | Sí |
| **3** | Renombre `api/`→`app/`; actualizar systemd/Nginx/docs; sacar indexación del arranque (§6) | **Alto** (requiere tocar el servidor) | Con plan de rollback |
| **4** | `Dockerfile` real; CI (pytest + lint); health checks robustos | Bajo | Sí |

Cada fase es desplegable y verificable de forma independiente.

---

## 10. Checklist de verificación por fase

- [ ] **Fase 0:** `pytest` corre; la API sigue levantando con `gunicorn api.main:app`.
- [ ] **Fase 1:** `/health` OK; CORS validado; `/reindexar` rechaza sin `ADMIN_TOKEN`; logs sin secretos.
- [ ] **Fase 2:** todos los endpoints responden igual; sin duplicación de `_build_document_urls`.
- [ ] **Fase 3:** systemd actualizado y servicio `active`; `curl https://bots.tech-energy.lat/health` OK; docs actualizadas.
- [ ] **Fase 4:** build de Docker OK; CI en verde.
```
