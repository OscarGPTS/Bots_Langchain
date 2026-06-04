# 🎙️ Guía de integración — Servicio de Voz (para app cliente)

Cómo consumir el servicio de voz del RAG desde una aplicación externa: enviar audio,
recibir la respuesta en **texto y/o voz**.

---

## 1. Resumen del flujo

```
Tu app  ──(audio: webm/wav/mp3)──▶  POST /api/v1/voz/consulta
                                         │
                                         ▼
                          STT → RAG (documentos) → TTS
                                         │
        ◀──── JSON {texto + audio_base64}  o  audio/wav ────┘
```

Una sola llamada hace todo: transcribe el audio, consulta los documentos y devuelve
la respuesta. Tú eliges si quieres la respuesta como **texto**, **audio** o **ambos**.

---

## 2. Información general

| Dato | Valor |
|---|---|
| **Base URL (producción)** | `https://bots.tech-energy.lat` |
| **Base URL (local/dev)** | `http://localhost:8000` |
| **Endpoint principal** | `POST /api/v1/voz/consulta` |
| **Health** | `GET /api/v1/voz/health` |
| **Autenticación** | Gestionada por Cloudflare Zero Trust (perímetro). El endpoint de voz **no** requiere header de auth propio. |
| **Documentación interactiva** | `/docs` (Swagger) · `/redoc` |

> ℹ️ Si tu app es un frontend en navegador y llama directo a `bots.tech-energy.lat`,
> ten en cuenta **CORS** y la política de Cloudflare Access (puede requerir que el
> usuario esté autenticado en el dominio). Para apps backend-a-backend no aplica CORS.

---

## 3. `POST /api/v1/voz/consulta`

### Request

- **Content-Type:** `multipart/form-data`
- **Campos:**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | archivo (binario) | ✅ | Audio de la pregunta. Formatos: `webm`, `wav`, `mp3`, `ogg`, `m4a`. |
| `formato_respuesta` | string | ❌ (default `ambos`) | `texto` · `audio` · `ambos` |

- **Límites:** tamaño máx. ~25 MB. Duración recomendada ≤ 60 s.
- El navegador normalmente graba en `webm/opus` con `MediaRecorder`: es compatible.

### Response según `formato_respuesta`

#### `texto` → `application/json`
```json
{
  "pregunta_transcrita": "¿Cuál es el horario de trabajo?",
  "respuesta": "El horario de trabajo es de lunes a viernes de 8:00 a 17:00...",
  "audio_base64": null,
  "tiempo_respuesta": 4.2
}
```

#### `ambos` → `application/json`  (texto + audio en base64)
```json
{
  "pregunta_transcrita": "¿Cuál es el horario de trabajo?",
  "respuesta": "El horario de trabajo es de lunes a viernes de 8:00 a 17:00...",
  "audio_base64": "UklGRiQAAABXQVZFZm10IB...(WAV en base64)...",
  "tiempo_respuesta": 5.8
}
```
> `audio_base64` es un **WAV** codificado en base64. Decodifícalo para reproducirlo.

#### `audio` → `audio/wav` (binario)
- El cuerpo de la respuesta es directamente el archivo WAV.
- La transcripción viaja en el header **`X-Pregunta-Transcrita`** y está
  **percent-encoded** → aplica `decodeURIComponent()` (JS) / `urllib.parse.unquote()` (Python).

### Campos de la respuesta JSON

| Campo | Tipo | Descripción |
|---|---|---|
| `pregunta_transcrita` | string | Lo que el STT entendió del audio |
| `respuesta` | string | Respuesta del RAG (incluye al final los documentos consultados) |
| `audio_base64` | string \| null | WAV en base64 (solo con `formato=ambos`; `null` con `texto`) |
| `tiempo_respuesta` | number | Segundos totales (STT + RAG + TTS) |

### Códigos de estado

| Código | Significado |
|---|---|
| `200` | OK |
| `413` | Audio demasiado grande (> 25 MB) |
| `422` | Audio vacío o no se pudo transcribir |
| `503` | Módulo de voz deshabilitado o dependencias faltantes en el servidor |
| `500` | Error interno |

Cuerpo de error: `{ "detail": "mensaje" }`.

---

## 4. `GET /api/v1/voz/health`

Útil para verificar que el servicio está listo antes de habilitar el botón de voz.

```json
{
  "voice_enabled": true,
  "stt_provider": "local",
  "tts_provider": "local",
  "ffmpeg_disponible": true,
  "faster_whisper_disponible": true,
  "piper_disponible": true,
  "voz_piper_existe": true,
  "openai_disponible": true,
  "backend_rag": "simple",
  "whisper_model": "small"
}
```
Si `voice_enabled` es `false`, `/consulta` responderá `503`.

---

## 5. Ejemplos de integración

### 5.1. Navegador — grabar micrófono y enviar (JavaScript)

```javascript
const BASE_URL = "https://bots.tech-energy.lat";

// 1) Grabar audio del micrófono
async function grabar(segundos = 5) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
  const chunks = [];
  rec.ondataavailable = (e) => chunks.push(e.data);
  rec.start();
  await new Promise((r) => setTimeout(r, segundos * 1000));
  rec.stop();
  await new Promise((r) => (rec.onstop = r));
  stream.getTracks().forEach((t) => t.stop());
  return new Blob(chunks, { type: "audio/webm" });
}

// 2) Enviar al servicio de voz (formato "ambos": texto + audio)
async function consultarVoz(audioBlob) {
  const form = new FormData();
  form.append("file", audioBlob, "pregunta.webm");
  form.append("formato_respuesta", "ambos");

  const resp = await fetch(`${BASE_URL}/api/v1/voz/consulta`, {
    method: "POST",
    body: form, // NO pongas Content-Type manual: el navegador agrega el boundary
  });
  if (!resp.ok) throw new Error(`Error ${resp.status}: ${(await resp.json()).detail}`);
  return resp.json();
}

// 3) Reproducir el audio de la respuesta (base64 → WAV)
function reproducirBase64Wav(audioB64) {
  const bytes = Uint8Array.from(atob(audioB64), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  new Audio(url).play();
}

// Uso
const blob = await grabar(5);
const data = await consultarVoz(blob);
console.log("Pregunta:", data.pregunta_transcrita);
console.log("Respuesta:", data.respuesta);
if (data.audio_base64) reproducirBase64Wav(data.audio_base64);
```

### 5.2. Navegador — solo audio (stream binario)

```javascript
async function consultarVozAudio(audioBlob) {
  const form = new FormData();
  form.append("file", audioBlob, "pregunta.webm");
  form.append("formato_respuesta", "audio");

  const resp = await fetch(`${BASE_URL}/api/v1/voz/consulta`, { method: "POST", body: form });
  if (!resp.ok) throw new Error(`Error ${resp.status}`);

  // Transcripción en el header (percent-encoded)
  const pregunta = decodeURIComponent(resp.headers.get("X-Pregunta-Transcrita") || "");
  const wavBlob = await resp.blob(); // audio/wav
  new Audio(URL.createObjectURL(wavBlob)).play();
  return pregunta;
}
```

### 5.3. Python (requests)

```python
import base64
import requests

BASE_URL = "https://bots.tech-energy.lat"

with open("pregunta.wav", "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/api/v1/voz/consulta",
        files={"file": ("pregunta.wav", f, "audio/wav")},
        data={"formato_respuesta": "ambos"},
        timeout=120,
    )
resp.raise_for_status()
data = resp.json()

print("Pregunta:", data["pregunta_transcrita"])
print("Respuesta:", data["respuesta"])

if data.get("audio_base64"):
    with open("respuesta.wav", "wb") as out:
        out.write(base64.b64decode(data["audio_base64"]))
    print("Audio guardado en respuesta.wav")
```

### 5.4. cURL

```bash
# Respuesta en texto
curl -X POST "https://bots.tech-energy.lat/api/v1/voz/consulta" \
  -F "file=@pregunta.wav" \
  -F "formato_respuesta=texto"

# Respuesta en audio (guardar el WAV)
curl -X POST "https://bots.tech-energy.lat/api/v1/voz/consulta" \
  -F "file=@pregunta.wav" \
  -F "formato_respuesta=audio" \
  --output respuesta.wav
```

---

## 6. Notas para el desarrollador cliente

- **No fijes `Content-Type` manualmente** en `multipart`: deja que la librería/navegador
  ponga el `boundary` automáticamente.
- **Idioma:** el STT está fijado a español (`es`).
- **Latencia:** depende del servidor. Con STT local en CPU puede tardar varios segundos
  (incluye transcripción + RAG + síntesis). Usa un `timeout` ≥ 120 s y muestra un *loading*.
- **`respuesta`** incluye, al final, la lista de "Documentos consultados". Si solo quieres
  el texto hablado, el audio ya viene limpio de esa sección (el servidor lo recorta para TTS).
- **Reintentos:** ante `503`, el módulo puede estar deshabilitado o iniciándose; reintenta
  o consulta `/health`.
- **Tamaño:** comprime/limita la duración del audio en el cliente para no acercarte al límite.

---

## 7. Cambios que pueden afectar al cliente (versionado)

- El contrato JSON (`pregunta_transcrita`, `respuesta`, `audio_base64`, `tiempo_respuesta`)
  es estable. Trata `audio_base64` como opcional (`null` cuando `formato=texto`).
- El proveedor STT/TTS (local u OpenAI) es transparente para el cliente: **no cambia el
  contrato**, solo la calidad/latencia de la voz.
