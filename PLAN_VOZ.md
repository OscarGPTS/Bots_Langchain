# 🎙️ Plan — Servicio de Voz (STT + RAG + TTS)

> **Estado:** Propuesta para revisión. **No** se ha modificado código.
> **Decisiones tomadas:**
> - Enfoque: **local / open-source como principal** (faster-whisper + Piper), con diseño **híbrido** (switch de proveedor por etapa) para contemplar también nube.
> - **Módulo integrado** en la app (no microservicio, por ahora) con **carga perezosa** del modelo.
> - **Sin GPU** → CPU. Modelo Whisper `small` (intercambiable). Voz Piper acento **`es_MX`**.
> - STT y TTS: **solo local** en la práctica (la nube de audio requeriría API key de OpenAI, no la cubre OpenCode Go).
> - Etapa de respuesta (LLM): contempla **Ollama local (principal)**, **OpenCode Go gateway** y **OpenAI**.
> - Entrega: plan detallado primero (este documento).
> **Fecha:** 2026-06-01

---

## 1. Idea y alcance

Permitir consultar el RAG **por voz**: el usuario envía audio, se transcribe a texto,
se consulta la base de documentos existente y se devuelve la respuesta como **texto,
voz, o ambos**.

> 💡 La parte difícil ya existe (el RAG sobre Paperless). El servicio de voz es solo
> una **capa de entrada/salida** que envuelve la consulta actual. No se toca la lógica RAG.

### Qué aporta (y qué no) tu plan OpenCode Go
**OpenCode Go** da acceso a **modelos de lenguaje de texto** (GLM, Kimi, Qwen, MiniMax,
DeepSeek, …) vía un endpoint **compatible con OpenAI** (`base_url` + API key). Por lo tanto:

- ❌ **No** hace STT (voz→texto) ni TTS (texto→voz): son LLM de texto. El audio sigue **local** (faster-whisper + Piper).
- ✅ **Sí** sirve para la **etapa de generación de la respuesta del RAG**, como alternativa de nube a tu Ollama local.

Como `langchain-openai.ChatOpenAI` acepta `base_url` personalizada, el gateway de OpenCode
se integra reutilizando el cliente OpenAI existente del bot avanzado (mismo código, otra URL).

### Diseño híbrido (3 etapas independientes)
Cada etapa tiene su propio switch de proveedor; el **local es el principal**:

| Etapa | Local (principal) | Nube (opcional) | ¿OpenCode Go? |
|---|---|---|---|
| 1. STT | faster-whisper | OpenAI `whisper-1` (API key OpenAI) | ❌ |
| 2. LLM respuesta | Ollama (`phi4-mini`) | **OpenCode gateway** / OpenAI | ✅ |
| 3. TTS | Piper (`es_MX`) | OpenAI `tts-1` (API key OpenAI) | ❌ |

Patrón recomendado: **local primero, nube opcional o como fallback** configurable, para poder
comparar cuál te sirve mejor sin reescribir nada.

---

## 2. Arquitectura

```
🎙️ Audio (micrófono del frontend o archivo subido)
      │  POST /api/v1/voz/consulta   (multipart/form-data: file=<audio>)
      ▼
┌──────────────────────────────────────────────┐
│ 1. Normalizar audio (ffmpeg → wav 16kHz mono) │
│ 2. STT: faster-whisper → texto                │   app/clients/stt.py
└──────────────────────────────────────────────┘
      ▼
   RAG existente (bot simple o avanzado)  →  respuesta en texto
      ▼
┌──────────────────────────────────────────────┐
│ 3. TTS: Piper → audio wav   (opcional)        │   app/clients/tts.py
└──────────────────────────────────────────────┘
      ▼
   Respuesta:
     - modo "texto":  { "pregunta_transcrita": "...", "respuesta": "..." }
     - modo "audio":  audio/wav (streaming)
     - modo "ambos":  JSON con respuesta en texto + audio en base64
```

---

## 3. Componentes y librerías

| Componente | Librería | Por qué | Modelo recomendado (español) |
|---|---|---|---|
| **STT** | [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) | Whisper reimplementado en CTranslate2: 4× más rápido y menos RAM que `openai-whisper`. CPU o GPU. | `small` (equilibrio) o `medium` (más preciso, más lento) |
| **TTS** | [`piper-tts`](https://github.com/rhasspy/piper) | Rápido, ligero, offline, voces neuronales en español. | `es_MX-*` o `es_ES-*` (voces en rhasspy/piper-voices) |
| **Audio** | `ffmpeg` (binario del SO) | El navegador graba en `webm/opus`; Whisper necesita PCM. ffmpeg normaliza a wav 16kHz mono. | — |

> Alternativas consideradas y descartadas para esta fase: `whisper.cpp` (requiere compilar),
> Vosk (peor calidad en español), Coqui XTTS (pesado, clonación de voz innecesaria aquí).

---

## 4. Estructura de archivos nueva

Encaja en la estructura ya reestructurada:

```
app/
├── clients/
│   ├── stt.py              # NUEVO: carga faster-whisper (singleton) y transcribe
│   └── tts.py              # NUEVO: invoca Piper y devuelve wav
├── services/
│   └── voz.py              # NUEVO: orquesta STT → RAG → TTS
├── api/v1/endpoints/
│   └── voz.py              # NUEVO: POST /api/v1/voz/consulta (+ /health)
├── schemas/
│   └── (añadir) VozResponse, VozTextoResponse
└── core/
    └── config.py           # (añadir) settings de voz
scripts/
└── descargar_modelos_voz.py  # NUEVO: descarga modelo Whisper + voz Piper
```

El router v1 (`app/api/v1/router.py`) incluirá el nuevo `voz_router`.

---

## 5. Configuración nueva (`app/core/config.py`)

| Variable | Default | Descripción |
|---|---|---|
| `VOICE_ENABLED` | `false` | Activa el módulo de voz (si las deps no están instaladas, se mantiene apagado). |
| `STT_PROVIDER` | `local` | `local` (faster-whisper) o `openai` (whisper-1, requiere API key OpenAI). |
| `WHISPER_MODEL` | `small` | Modelo faster-whisper (`tiny`/`base`/`small`/`medium`/`large-v3`). |
| `WHISPER_DEVICE` | `cpu` | `cpu` o `cuda` (si hay GPU). |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` (CPU) o `float16` (GPU). |
| `STT_LANGUAGE` | `es` | Idioma fijo para mejor precisión/velocidad. |
| `TTS_PROVIDER` | `local` | `local` (Piper) o `openai` (tts-1, requiere API key OpenAI). |
| `PIPER_VOICE_PATH` | `models/piper/es_MX-xxx.onnx` | Ruta al modelo de voz Piper (acento `es_MX`). |
| `VOICE_MAX_SECONDS` | `60` | Duración máxima de audio aceptada (anti-abuso). |
| `VOICE_BACKEND` | `simple` | Qué bot RAG usa la voz: `simple` o `avanzado`. |

**Etapa LLM de la respuesta (reutiliza/extiende la config existente):**

| Variable | Default | Descripción |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` (local, principal) · `opencode` (gateway) · `openai`. Generaliza el actual `LOCALIA`. |
| `OPENCODE_BASE_URL` | — | URL del gateway OpenCode (endpoint compatible con OpenAI). |
| `OPENCODE_API_KEY` | — | API key de OpenCode Go. |
| `OPENCODE_MODEL` | — | Modelo a usar (p.ej. `deepseek-v4-pro`, `qwen3.7-max`, etc.). |

> `LLM_PROVIDER` sustituye conceptualmente a `LOCALIA` (que se mantiene por compatibilidad:
> `LOCALIA=true` ⇒ `ollama`). Así contemplas los tres casos sin romper lo existente.

Mismo patrón que `LOCALIA`: una sola fuente de verdad, validada al arranque.

---

## 6. Contrato de la API

### `POST /api/v1/voz/consulta`
- **Entrada:** `multipart/form-data`
  - `file`: archivo de audio (`webm`, `wav`, `mp3`, `ogg`, `m4a`)
  - `formato_respuesta` (query/form, opcional): `texto` | `audio` | `ambos` (default `ambos`)
- **Salida según `formato_respuesta`:**
  - `texto` → `application/json`:
    ```json
    {
      "pregunta_transcrita": "¿cuál es el horario de trabajo?",
      "respuesta": "El horario es de lunes a viernes de 8 a 17h...",
      "tiempo_respuesta": 4.2
    }
    ```
  - `audio` → `audio/wav` (StreamingResponse) con header `X-Pregunta-Transcrita`
  - `ambos` → JSON con `respuesta` (texto) + `audio_base64` (wav en base64)

### `GET /api/v1/voz/health`
Reporta si el módulo está habilitado, modelo Whisper cargado, voz Piper disponible y `ffmpeg` presente.

> Reutiliza el RAG existente: internamente llama al mismo `bot.procesar()` / `consulta_rapida()`
> que ya usan los endpoints de texto. **Cero cambios en la lógica RAG.**

---

## 7. Dependencias e instalación en el servidor (Ubuntu 24.04)

```bash
# 1. Binario del sistema
sudo apt update && sudo apt install -y ffmpeg

# 2. Dependencias Python (en el venv del proyecto)
source /home/www/Bots_Langchain/.venv/bin/activate
pip install faster-whisper piper-tts

# 3. Descargar modelos (script nuevo)
python scripts/descargar_modelos_voz.py
#   - faster-whisper 'small' se descarga solo al primer uso (cache en ~/.cache)
#   - Piper: descargar el .onnx + .onnx.json de una voz española a models/piper/
#     (repo: https://huggingface.co/rhasspy/piper-voices/tree/main/es)
```

Se añadirán a `requirements.txt` / `pyproject.toml`:
`faster-whisper`, `piper-tts`. (ffmpeg es del SO, no de pip.)

`.gitignore`: añadir `models/` (los `.onnx` pesan; no versionar).

---

## 8. ⚠️ Consideraciones de recursos (clave con Gunicorn 4 workers)

Igual que con la indexación, **cada worker carga su propia copia del modelo Whisper** →
multiplica RAM:

| Modelo Whisper | RAM aprox. por worker | ×4 workers |
|---|---|---|
| `small` | ~0.5–1 GB | ~2–4 GB |
| `medium` | ~1.5–2 GB | ~6–8 GB |

**Estrategias (a elegir en la fase de implementación):**
1. **Carga perezosa (lazy) + singleton por worker:** el modelo se carga en RAM solo en la
   primera petición de voz, no al arrancar. Simple; recomendado para empezar.
2. **Microservicio de voz aparte:** un proceso/servicio dedicado (1–2 workers) solo para voz,
   separado de la API principal. Encaja con tu rama `microservicios-doc`. Aísla la RAM y la
   latencia del STT del resto de la API. Recomendado si el uso de voz crece.
3. Usar modelo `small` y `WHISPER_COMPUTE_TYPE=int8` para minimizar RAM en CPU.

> Empezaría con la opción 1 (lazy, en la misma app) y dejaría la 2 documentada como evolución.

---

## 9. Seguridad

- **Perímetro:** mismo Cloudflare Zero Trust; no se añade auth propia (coherente con la decisión previa).
- **Límite de tamaño:** Nginx ya tiene `client_max_body_size 50M`. Validar además duración (`VOICE_MAX_SECONDS`) y tipo MIME del audio.
- **ffmpeg:** ejecutar con argumentos fijos sobre archivos temporales; nunca interpolar rutas/entrada del usuario en shell. Usar `subprocess` con lista de args (sin `shell=True`).
- **Archivos temporales:** escribir en `tempfile`, borrar siempre (try/finally).
- **No registrar audio ni transcripciones con datos sensibles** en logs (coherente con la política de logging).

---

## 10. Rendimiento / latencia

- STT es el cuello de botella. En CPU, `small` ≈ 2–5 s para ~10 s de audio; `medium` más.
  Con GPU (`cuda`/`float16`) baja a <1 s.
- Piper (TTS) es muy rápido (décimas de segundo por frase).
- El timeout de Gunicorn/Nginx (300 s) ya cubre de sobra.
- Posible mejora futura: transcripción en streaming / WebSocket (más complejo; fuera de alcance inicial).

---

## 11. Fases de ejecución

| Fase | Contenido | Riesgo |
|---|---|---|
| **V0** | Deps (`ffmpeg`, `faster-whisper`, `piper-tts`) + `scripts/descargar_modelos_voz.py` + settings de voz | Bajo |
| **V1** | `app/clients/stt.py` (lazy singleton) + endpoint `POST /voz/consulta` que devuelve **solo texto** (prueba de flujo STT → RAG) | Bajo |
| **V2** | `app/clients/tts.py` (Piper) + `formato_respuesta` (`audio`/`ambos`) + `service/voz.py` | Medio |
| **V3** | `/voz/health`, validaciones (duración, MIME), docs (README/API_DOCUMENTATION) | Bajo |
| **V4** (opcional) | Separar como microservicio de voz dedicado (opción 8.2) | Medio |

---

## 12. Checklist de verificación

- [ ] **V0:** `ffmpeg -version` OK en el servidor; `pip show faster-whisper piper-tts` OK; modelo Piper descargado en `models/piper/`.
- [ ] **V1:** `POST /api/v1/voz/consulta` con un wav de prueba devuelve la transcripción + respuesta de texto correcta.
- [ ] **V2:** `formato_respuesta=audio` devuelve un wav reproducible; `ambos` devuelve texto + base64.
- [ ] **V3:** `/voz/health` reporta estado; audios > límite se rechazan con 413/422.
- [ ] RAM del servidor estable con 4 workers tras varias consultas de voz (verificar opción lazy).

---

## 13. Decisiones (confirmadas) y pendientes

**Confirmadas:**
- ✅ Módulo **integrado** con carga perezosa (no microservicio por ahora).
- ✅ STT/TTS **local como principal**; diseño híbrido con switch de proveedor por etapa.
- ✅ **Sin GPU** → CPU, `WHISPER_COMPUTE_TYPE=int8`.
- ✅ Modelo Whisper **`small`** (intercambiable a `medium` si la precisión en español no alcanza — es cosa de probar).
- ✅ Voz Piper acento **`es_MX`**.
- ✅ OpenCode Go se integra **solo en la etapa LLM** (no audio), como alternativa de nube a Ollama.

**Pendientes (no bloquean V0/V1):**
1. **Voz Piper concreta:** ¿masculina o femenina? (elegir un `.onnx` específico de `es_MX` en el repo de Piper).
2. **Modelo OpenCode** a usar por defecto cuando se pruebe la nube (p.ej. DeepSeek vs Qwen vs GLM) — se decide al comparar.
3. Confirmar que el gateway de OpenCode es **compatible con la API de OpenAI** (base_url + key). Si usa otro formato, se añade un cliente específico.
