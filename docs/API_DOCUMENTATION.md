# 📚 Documentación API - Bots de Documentos

## 🌐 Información General

### URLs Base

**Producción:**
```
https://bots.tech-energy.lat
```

**Local (Desarrollo):**
```
http://localhost:8000
```

### Autenticación

Actualmente la API **no requiere autenticación**. En producción está protegida por Cloudflare Zero Trust a nivel de infraestructura.

### Formato de Respuestas

Todas las respuestas son en formato **JSON** con estructura estandarizada.

### Documentación Interactiva

- **Swagger UI**: `https://bots.tech-energy.lat/docs`
- **ReDoc**: `https://bots.tech-energy.lat/redoc`
- **OpenAPI JSON**: `https://bots.tech-energy.lat/openapi.json`

---

## 🤖 Bot Simple

Base URL: `/api/v1/bot-simple`

### 1. Health Check

**Endpoint:** `GET /api/v1/bot-simple/health`

**Descripción:** Verificar estado del bot simple y componentes.

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-simple/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-17T18:41:56.996279",
  "ia_disponible": true,
  "chromadb_disponible": true,
  "paperless_conectado": true,
  "total_documentos": 2
}
```

**Campos de Response:**
- `status` (string): Estado del servicio (`healthy` o `degraded`)
- `version` (string): Versión de la API
- `timestamp` (string): Timestamp ISO 8601
- `ia_disponible` (boolean): IA (Ollama) disponible
- `chromadb_disponible` (boolean): ChromaDB operativo
- `paperless_conectado` (boolean): Conexión con Paperless activa
- `total_documentos` (integer): Total de documentos indexados

---

### 2. Consulta General

**Endpoint:** `POST /api/v1/bot-simple/query`

**Descripción:** Realizar consulta general con búsqueda semántica y generación de respuesta con IA.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-simple/query" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Qué dice el código de ética sobre integridad?"
  }'
```

**Request Body:**
```json
{
  "pregunta": "¿Qué dice el código de ética sobre integridad?"
}
```

**Campos de Request:**
- `pregunta` (string, required): Pregunta o consulta del usuario (mínimo 3 caracteres)

**Response:**
```json
{
  "respuesta": "El código de ética define la integridad como...",
  "tiempo_respuesta": 2.5
}
```

**Campos de Response:**
- `respuesta` (string): Respuesta generada por el bot
- `tiempo_respuesta` (float): Tiempo de procesamiento en segundos

---

### 3. Analizar Documento Específico

**Endpoint:** `POST /api/v1/bot-simple/analyze-document`

**Descripción:** Analizar documento por ID. Si no se proporciona pregunta, genera resumen ejecutivo.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-simple/analyze-document" \
  -H "Content-Type: application/json" \
  -d '{
    "documento_id": 1,
    "pregunta": "¿Cuáles son los puntos clave?"
  }'
```

**Request Body:**
```json
{
  "documento_id": 1,
  "pregunta": "¿Cuáles son los puntos clave de este documento?"
}
```

**Campos de Request:**
- `documento_id` (integer, required): ID del documento en Paperless (mayor a 0)
- `pregunta` (string, optional): Pregunta específica sobre el documento

**Response:**
```json
{
  "respuesta": "Los puntos clave del documento son: 1) ...",
  "tiempo_respuesta": 3.1
}
```

---

### 4. Listar Todos los Documentos

**Endpoint:** `GET /api/v1/bot-simple/documents`

**Descripción:** Obtener lista de documentos de Paperless con formato JSON estandarizado.

**Query Parameters:**
- `limite` (integer, optional): Número máximo de documentos (default: 100)

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-simple/documents?limite=10"
```

**Response:**
```json
{
  "documentos": [
    {
      "id": 3,
      "title": "Reglamento Interno de Trabajo GPT Services",
      "created": "2026-03-11",
      "modified": "2026-03-11T16:21:45.158706Z",
      "content": null,
      "archive_serial_number": null,
      "correspondent": null,
      "document_type": null,
      "tags": []
    },
    {
      "id": 4,
      "title": "Reglamento de Acceso a las instalaciones",
      "created": "2026-03-11",
      "modified": "2026-03-11T20:30:53.805038Z",
      "content": null,
      "archive_serial_number": null,
      "correspondent": null,
      "document_type": null,
      "tags": []
    }
  ],
  "total": 2,
  "tiempo_respuesta": 0.22
}
```

**Campos de Response:**
- `documentos` (array): Lista de documentos
  - `id` (integer): ID del documento en Paperless
  - `title` (string): Título del documento
  - `created` (string): Fecha de creación (YYYY-MM-DD)
  - `modified` (string): Fecha de modificación (ISO 8601)
  - `content` (string|null): Contenido del documento
  - `archive_serial_number` (integer|null): Número de archivo
  - `correspondent` (integer|null): ID del corresponsal
  - `document_type` (integer|null): ID del tipo de documento
  - `tags` (array): IDs de tags asociados
  - `download_url` (string): URL para descargar el documento original
  - `preview_url` (string): URL para visualizar/preview del documento
  - `thumbnail_url` (string): URL para thumbnail (miniatura) del documento
- `total` (integer): Total de documentos retornados
- `tiempo_respuesta` (float): Tiempo de procesamiento en segundos

**📌 Nota sobre URLs de documentos:**
Los campos `download_url`, `preview_url` y `thumbnail_url` permiten acceso directo a los documentos en Paperless:
- **download_url**: Descarga el archivo original (PDF, imagen, etc.)
- **preview_url**: Visualización del documento en navegador (ideal para iframes)
- **thumbnail_url**: Miniatura del documento (ideal para listados/grids)

✅ **Importante**: Las URLs ya incluyen el token de autenticación como query parameter (`?token=XXX`), por lo que:
- **Puedes abrirlas directamente** en el navegador o en un `<iframe>` sin configuración adicional
- **No necesitas agregar headers** de autenticación en el frontend
- Las URLs son privadas y contienen el token - no las expongas públicamente

Ejemplo de URL generada:
```
https://paperless.tech-energy.lat/api/documents/1/preview/?token=abc123def456
```

---

### 5. Listar Documentos Recientes

**Endpoint:** `GET /api/v1/bot-simple/recent-documents`

**Descripción:** Obtener lista de documentos recientes de Paperless (ordenados por fecha de creación).

**Query Parameters:**
- `limite` (integer, optional): Número de documentos a devolver (default: 10)

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-simple/recent-documents?limite=5"
```

**Response:**
```json
{
  "documentos": [
    {
      "id": 4,
      "title": "Reglamento de Acceso a las instalaciones",
      "created": "2026-03-11",
      "modified": "2026-03-11T20:30:53.805038Z",
      "content": null,
      "archive_serial_number": null,
      "correspondent": null,
      "document_type": null,
      "tags": []
    }
  ],
  "total": 1,
  "tiempo_respuesta": 0.23
}
```

---

## 🧠 Bot Avanzado

Base URL: `/api/v1/bot-avanzado`

### 1. Health Check

**Endpoint:** `GET /api/v1/bot-avanzado/health`

**Descripción:** Verificar estado del bot avanzado y componentes.

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-avanzado/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-17T18:42:04.934751",
  "ia_disponible": true,
  "chromadb_disponible": true,
  "paperless_conectado": true,
  "total_documentos": 4
}
```

---

### 2. Consulta Rápida

**Endpoint:** `POST /api/v1/bot-avanzado/consulta-rapida`

**Descripción:** Consulta rápida con 3 chunks y modelo rápido. Ideal para consultas simples.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-avanzado/consulta-rapida" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Cuál es el horario de trabajo?",
    "filtros": {"created": "2026"}
  }'
```

**Request Body:**
```json
{
  "pregunta": "¿Cuál es el horario de trabajo?",
  "filtros": {
    "created": "2026"
  }
}
```

**Campos de Request:**
- `pregunta` (string, required): Pregunta del usuario (mínimo 3 caracteres)
- `filtros` (object, optional): Filtros de metadata (año, tags, etc.)

**Response:**
```json
{
  "respuesta": "El horario de trabajo es de lunes a viernes de 8:00 AM a 5:00 PM...",
  "estadisticas": {
    "tokens_entrada": 150,
    "tokens_salida": 80,
    "costo_usd": 0.00015
  },
  "tiempo_respuesta": 3.2
}
```

**Campos de Response:**
- `respuesta` (string): Respuesta generada
- `estadisticas` (object, optional): Estadísticas de uso
  - `tokens_entrada` (integer): Tokens de entrada
  - `tokens_salida` (integer): Tokens de salida
  - `costo_usd` (float): Costo en USD (si aplica)
- `tiempo_respuesta` (float): Tiempo en segundos

---

### 3. Razonamiento Profundo

**Endpoint:** `POST /api/v1/bot-avanzado/razonamiento-profundo`

**Descripción:** Análisis profundo con hasta 20 chunks. Ideal para preguntas complejas y comparaciones.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-avanzado/razonamiento-profundo" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "Analiza las políticas de vacaciones y compáralas con la legislación",
    "filtros": null,
    "k": 10
  }'
```

**Request Body:**
```json
{
  "pregunta": "Analiza las políticas de vacaciones y compáralas con la legislación",
  "filtros": null,
  "k": 10
}
```

**Campos de Request:**
- `pregunta` (string, required): Pregunta compleja para análisis (mínimo 3 caracteres)
- `filtros` (object, optional): Filtros de metadata
- `k` (integer, optional): Número de chunks a analizar (1-20, default: 10)

**Response:**
```json
{
  "respuesta": "Análisis detallado de políticas de vacaciones...",
  "estadisticas": {
    "tokens_entrada": 450,
    "tokens_salida": 320,
    "costo_usd": 0.00082
  },
  "tiempo_respuesta": 8.5
}
```

---

### 4. Búsqueda Semántica

**Endpoint:** `POST /api/v1/bot-avanzado/busqueda-semantica`

**Descripción:** Búsqueda semántica sin generación de respuesta. Devuelve chunks más similares.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-avanzado/busqueda-semantica" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "políticas de seguridad",
    "k": 5,
    "filtros": null
  }'
```

**Request Body:**
```json
{
  "query": "políticas de seguridad",
  "k": 5,
  "filtros": null
}
```

**Campos de Request:**
- `query` (string, required): Consulta de búsqueda (mínimo 3 caracteres)
- `k` (integer, optional): Número de resultados (1-20, default: 5)
- `filtros` (object, optional): Filtros de metadata

**Response:**
```json
{
  "resultados": [
    {
      "doc_id": "3",
      "title": "Código de Ética",
      "chunk_index": 5,
      "total_chunks": 20,
      "created": "2026-03-10",
      "preview": "La integridad se define como...",
      "score": 0.92
    }
  ],
  "total": 1,
  "tiempo_respuesta": 0.8
}
```

**Campos de Response:**
- `resultados` (array): Lista de chunks encontrados
  - `doc_id` (string): ID del documento
  - `title` (string): Título del documento
  - `chunk_index` (integer): Índice del chunk en el documento
  - `total_chunks` (integer): Total de chunks del documento
  - `created` (string): Fecha de creación
  - `preview` (string): Preview del contenido (primeros 200 caracteres)
  - `score` (float, optional): Score de similitud
- `total` (integer): Número de resultados encontrados
- `tiempo_respuesta` (float): Tiempo en segundos

---

### 5. Estadísticas

**Endpoint:** `GET /api/v1/bot-avanzado/stats`

**Descripción:** Obtener estadísticas del bot avanzado (documentos, vectores, modelos).

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-avanzado/stats"
```

**Response:**
```json
{
  "total_documentos": 4,
  "total_vectores": 116,
  "modo": "cloud (OpenAI)",
  "modelo_rapido": "gpt-4o-mini",
  "modelo_razonamiento": "gpt-4o",
  "documentos_indexados": []
}
```

**Campos de Response:**
- `total_documentos` (integer): Total de documentos indexados
- `total_vectores` (integer): Total de vectores en ChromaDB
- `modo` (string): Modo actual (`local (Ollama)` o `cloud (OpenAI)`)
- `modelo_rapido` (string): Modelo configurado para consultas rápidas
- `modelo_razonamiento` (string): Modelo configurado para razonamiento profundo
- `documentos_indexados` (array): Lista de documentos indexados

---

### 6. Reindexar Documentos

**Endpoint:** `POST /api/v1/bot-avanzado/reindexar`

**Descripción:** Forzar reindexación de todos los documentos. **ADVERTENCIA**: Esta operación puede tardar varios minutos.

**Request:**
```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/bot-avanzado/reindexar" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "mensaje": "Reindexación completada",
  "documentos_nuevos": 2,
  "documentos_actualizados": 4,
  "tiempo_total": 45.8
}
```

**Campos de Response:**
- `mensaje` (string): Mensaje de confirmación
- `documentos_nuevos` (integer): Documentos nuevos agregados
- `documentos_actualizados` (integer): Total de documentos indexados
- `tiempo_total` (float): Tiempo total de reindexación en segundos

---

### 7. Listar Todos los Documentos

**Endpoint:** `GET /api/v1/bot-avanzado/documents`

**Descripción:** Obtener lista completa de documentos de Paperless.

**Query Parameters:**
- `limite` (integer, optional): Número máximo de documentos (default: 100)

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-avanzado/documents?limite=10"
```

**Response:** (Igual estructura que Bot Simple `/documents`)

---

### 8. Listar Documentos Recientes

**Endpoint:** `GET /api/v1/bot-avanzado/recent-documents`

**Descripción:** Obtener lista de documentos recientes de Paperless.

**Query Parameters:**
- `limite` (integer, optional): Número de documentos (default: 10)

**Request:**
```bash
curl -X GET "https://bots.tech-energy.lat/api/v1/bot-avanzado/recent-documents?limite=5"
```

**Response:** (Igual estructura que Bot Simple `/recent-documents`)

---

## 🎙️ Servicio de Voz

Base URL: `/api/v1/voz`

STT/TTS conmutables por proveedor (`STT_PROVIDER` / `TTS_PROVIDER`):
- **local** (default): faster-whisper + Piper. Requiere `ffmpeg` y modelos descargados
  (`python scripts/descargar_modelos_voz.py`).
- **openai**: usa la API de OpenAI (`whisper-1` para STT, `tts-1` para TTS). Requiere
  `OPENAI_API_KEY`. ⚠️ El audio se envía a OpenAI (considerar privacidad y costo).

Requiere `VOICE_ENABLED=true`.

### 1. Consulta por voz

**Endpoint:** `POST /api/v1/voz/consulta`

**Descripción:** Recibe audio, lo transcribe, consulta el RAG y responde en texto y/o voz.

**Request:** `multipart/form-data`
- `file` (requerido): archivo de audio (`webm`, `wav`, `mp3`, `ogg`, `m4a`)
- `formato_respuesta` (opcional): `texto` | `audio` | `ambos` (default `ambos`)

```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/voz/consulta" \
  -F "file=@pregunta.wav" \
  -F "formato_respuesta=ambos"
```

**Response según `formato_respuesta`:**
- `texto` → JSON:
  ```json
  {
    "pregunta_transcrita": "¿cuál es el horario de trabajo?",
    "respuesta": "El horario es de lunes a viernes de 8 a 17h...",
    "tiempo_respuesta": 4.2
  }
  ```
- `audio` → `audio/wav` (header `X-Pregunta-Transcrita`)
- `ambos` → JSON con `respuesta` (texto) + `audio_base64` (WAV en base64)

**Códigos:** `503` si el módulo está deshabilitado o faltan dependencias; `413` audio muy grande; `422` audio vacío/ininteligible.

### 2. Health del módulo de voz

**Endpoint:** `GET /api/v1/voz/health`

```json
{
  "voice_enabled": true,
  "ffmpeg_disponible": true,
  "faster_whisper_disponible": true,
  "piper_disponible": true,
  "voz_piper_existe": true,
  "backend_rag": "simple",
  "whisper_model": "small"
}
```

---

## 🗂️ Consultas a Datos (NL → SQL / API REST)

Consulta orígenes de datos (APIs REST y bases **MySQL de solo lectura**) a partir de lo
que diga el usuario (texto; la voz se transcribe antes). Un **catálogo de reglas**
(`config/rules.yaml`) define qué tablas/recursos hay y por qué *keys* se reconocen, para
acotar el contexto enviado al LLM. La respuesta es un **objeto estructurado**
(`texto` / `tabla` / `grafico`) que el frontend pinta (p. ej. con Chart.js).

> **Solo lectura.** El bot nunca escribe: SQL validado (solo `SELECT`/`WITH`, allowlist
> de tablas, `LIMIT` forzado) + usuario MySQL `GRANT SELECT` + transacción read-only.
> REST solo `GET` con allowlist de host y params. Requiere `CONSULTAS_ENABLED=true`.

### 1. Consultar datos

**Endpoint:** `POST /api/v1/consultas/`

**Request:**
```json
{
  "consulta": "Dame una tabla de todos los empleados",
  "origen": "rh_api",
  "formato": null,
  "usuario": "Óscar"
}
```
- `consulta` (string, required): lo que pide el usuario en lenguaje natural.
- `origen` (string, required): clave del origen en el catálogo (`rh_api`, `ventas_db`, …).
- `formato` (string, opcional): fuerza la salida → `texto` | `tabla` | `grafico`. Si se
  omite, la IA decide.
- `usuario` (string, opcional): nombre de quien consulta; personaliza el `texto`/audio
  de respuesta (p.ej. *"Óscar, aquí tienes el resultado: 87 registros."*).
- `objetivo` (string, opcional): **tabla (SQL) o recurso (REST) específico** a consultar.
  Si se indica, se ignora el matcher por palabras clave y la IA trabaja SOLO sobre esa
  entidad → más preciso y con menos errores. Ver "Consulta dirigida" abajo.

**Response (objeto estructurado):**
```json
{
  "origen": "rh_api",
  "tipo": "tabla",
  "titulo": "Empleados",
  "texto": "Se encontraron 87 resultado(s).",
  "tabla": {
    "columnas": ["nombre_completo", "email", "departamento", "area", "puesto", "activo"],
    "filas": [
      ["Ana López", "ana@x.com", "Sistemas", "TI", "Desarrolladora", true]
    ],
    "total_filas": 87,
    "truncado": false
  },
  "grafico": null,
  "meta": {
    "origen_tipo": "rest_api",
    "consulta_generada": "GET /users params={}",
    "candidatos": ["empleados"],
    "advertencias": []
  },
  "tiempo_respuesta": 1.4
}
```

---

### 📌 Ejemplo end-to-end con la API de RH

El origen `rh_api` mapea la API real de Recursos Humanos (`GET {API_RH_URL}/users` →
`{success, total, data:[...]}`). Cada empleado trae `nombre_completo`, `email`,
`telefono`, `activo` y los objetos `departamento{nombre}`, `area{nombre}`,
`puesto{nombre}`, `jefe_directo{nombre_completo}` (estos se aplanan a su `nombre`).

**Catálogo (`config/rules.yaml`):**
```yaml
origenes:
  rh_api:
    tipo: rest_api
    base_url_env: API_RH_URL          # https://services.satechenergy.com/api/rh
    timeout: 15
    recursos:
      - nombre: empleados
        keys: [empleado, empleados, usuario, usuarios, user, personal, colaborador, trabajador]
        endpoint: "/users"
        lista_en: "data"
        params_permitidos: []
```

#### a) Listado → `tabla`

```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/consultas/" \
  -H "Content-Type: application/json" \
  -d '{"consulta": "Lista de todos los empleados con su departamento", "origen": "rh_api"}'
```

El matcher detecta la key `empleados`, el LLM elige el recurso `empleados`, se hace
`GET /users`, se aplanan los registros y se devuelve `tipo: "tabla"`.

#### b) Visualización → `grafico` (FASE 2)

```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/consultas/" \
  -H "Content-Type: application/json" \
  -d '{"consulta": "Gráfica de cuántos empleados hay por departamento", "origen": "rh_api"}'
```

La API REST no agrega, así que el LLM marca `tipo: "grafico"` con
`agregacion: "conteo"` y la **agregación se hace del lado del servidor** (agrupando por
`departamento`). Respuesta:

```json
{
  "origen": "rh_api",
  "tipo": "grafico",
  "titulo": "Empleados por departamento",
  "texto": "Gráfico generado con 4 categoría(s).",
  "tabla": {
    "columnas": ["nombre_completo", "departamento"],
    "filas": [["Ana López", "Sistemas"], ["Luis Pérez", "Sistemas"], ["Eva Ruiz", "Ventas"]],
    "total_filas": 87,
    "truncado": false
  },
  "grafico": {
    "tipo_grafico": "bar",
    "etiquetas": ["Sistemas", "Ventas", "RH", "Operaciones"],
    "series": [{ "label": "conteo", "data": [12, 9, 5, 61] }]
  },
  "meta": { "origen_tipo": "rest_api", "consulta_generada": "GET /users params={}", "candidatos": ["empleados"], "advertencias": [] },
  "tiempo_respuesta": 1.8
}
```

> Se devuelve `grafico` **y** `tabla` (los datos crudos detrás del gráfico), para que el
> frontend muestre ambos si lo desea.

**Pintar el gráfico con Chart.js** (el objeto ya viene en formato compatible):
```javascript
const r = await fetch("/api/v1/consultas/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ consulta: "empleados por departamento", origen: "rh_api" })
}).then(x => x.json());

if (r.tipo === "grafico") {
  new Chart(document.getElementById("c"), {
    type: r.grafico.tipo_grafico,                 // "bar"
    data: {
      labels: r.grafico.etiquetas,                // ["Sistemas", ...]
      datasets: r.grafico.series                  // [{ label: "conteo", data: [...] }]
    }
  });
} else if (r.tipo === "tabla") {
  // pintar r.tabla.columnas / r.tabla.filas
} else {
  // r.texto
}
```

#### c) Ejemplo SQL (origen `ventas_db`)

```bash
curl -X POST ".../api/v1/consultas/" -H "Content-Type: application/json" \
  -d '{"consulta": "Total vendido por mes en 2026 en una gráfica de líneas", "origen": "ventas_db", "formato": "grafico"}'
```

Para SQL el LLM genera el `SELECT` con `GROUP BY`/`SUM` (la agregación ocurre en la BD),
se **valida como solo-lectura** y `meta.consulta_generada` devuelve el SQL ejecutado
(auditoría), p. ej.:
```sql
SELECT DATE_FORMAT(fecha,'%Y-%m') AS mes, SUM(total) AS total
FROM ordenes WHERE fecha >= '2026-01-01' GROUP BY mes ORDER BY mes LIMIT 500
```

---

### 🧪 Ejemplo LOCAL probado: BD `cartera_clientes` (MySQL/MariaDB)

Origen `cartera_db` mapeado al esquema real del proyecto Laravel (tablas `clientes`,
`contactos_cliente`, `proyectos`, `cotizaciones`, `users`).

**Configuración:**
```env
# .env
CONSULTAS_ENABLED=true
LLM_PROVIDER=opencode
CARTERA_DB_URL=mysql+pymysql://root@127.0.0.1:3306/cartera_clientes
```
```yaml
# config/rules.yaml  (extracto)
origenes:
  cartera_db:
    tipo: sql_mysql
    dsn_env: CARTERA_DB_URL
    tablas:
      - nombre: clientes
        keys: [cliente, clientes, cuenta, cartera, razon, empresa]
        columnas: [{nombre: razon_social}, {nombre: sector}, {nombre: activo}, ...]
      - nombre: proyectos
        keys: [proyecto, proyectos, oportunidad, oferta, cp, dn]
        columnas: [{nombre: monto_usd}, {nombre: estado}, {nombre: cliente_id}, ...]
```

**a) Listado → `tabla`** (`POST /api/v1/consultas/`):
```json
{ "consulta": "top 5 proyectos por monto en usd", "origen": "cartera_db" }
```
→ `tipo:"tabla"`, `meta.consulta_generada`:
```sql
SELECT id, cp_numero, dn_numero, monto_usd, estado FROM proyectos ORDER BY monto_usd DESC LIMIT 5
```

**b) Agregación → `grafico`** (Fase 2):
```json
{ "consulta": "cuántos clientes hay por sector", "origen": "cartera_db" }
```
→ `tipo:"grafico"` (la BD agrega con `GROUP BY`):
```json
{
  "tipo": "grafico",
  "titulo": "Clientes por sector",
  "grafico": {
    "tipo_grafico": "bar",
    "etiquetas": ["Oil & Gas", "Gasoductos", "Refinación", "Infraestructura", "Industrial"],
    "series": [{ "label": "cantidad", "data": [20, 16, 2, 2, 1] }]
  },
  "tabla": { "columnas": ["sector", "cantidad"], "total_filas": 6, "truncado": false },
  "meta": { "origen_tipo": "sql_mysql", "consulta_generada": "SELECT sector, COUNT(id) AS cantidad FROM clientes GROUP BY sector ORDER BY cantidad DESC LIMIT 500" }
}
```

**Probar desde Swagger:** abre **http://localhost:8000/docs** → grupo **Consultas** →
`POST /api/v1/consultas/` → *Try it out* → pega el body → *Execute*.

PowerShell:
```powershell
$body = @{ consulta = "cuántos clientes hay por sector"; origen = "cartera_db" } | ConvertTo-Json
Invoke-RestMethod "http://localhost:8000/api/v1/consultas/" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 8
```

> ⚠️ **Seguridad (entorno local):** `root` sin contraseña tiene permisos totales; aquí la
> garantía de solo-lectura recae en la **validación de SQL** + `SET SESSION TRANSACTION
> READ ONLY`. Para producción, crea un usuario con `GRANT SELECT` y usa ese DSN.

---

### 🎯 Consulta dirigida (`objetivo`) y relaciones (FK)

Para módulos específicos conviene **fijar la tabla/recurso** con `objetivo`, en vez de
dejar que el matcher la deduzca. Reduce ambigüedad y errores:

```json
{ "consulta": "estadísticas de los proyectos de este mes", "origen": "cartera_db", "objetivo": "proyectos" }
```

**Relaciones por clave foránea (JOIN).** Si la consulta cruza entidades (p.ej. proyectos
↔ cliente), declara la relación en `config/rules.yaml`. El generador recibe el JOIN y el
validador permite también la tabla relacionada (allowlist ampliada):

```yaml
tablas:
  - nombre: proyectos
    keys: [proyecto, proyectos, oportunidad, oferta]
    relaciones:
      - { tabla: clientes, on: "proyectos.cliente_id = clientes.id", descripcion: "Cliente del proyecto" }
    columnas: [ { nombre: monto_usd }, { nombre: cliente_id }, { nombre: fecha_envio }, ... ]
```

Ejemplo real validado — `objetivo: "proyectos"` + *"monto total por cliente, top 5"*:
```sql
SELECT c.razon_social, SUM(p.monto_usd) AS total_monto
FROM proyectos AS p JOIN clientes AS c ON p.cliente_id = c.id
GROUP BY c.id, c.razon_social ORDER BY total_monto DESC LIMIT 5
```
→ tabla con SEDENA $33.3M, Protexa $1.7M, … (`meta.candidatos = ["proyectos"]`).

> **Dos estrategias para limitar y reducir errores:** (1) `objetivo` + `relaciones` para
> que el LLM navegue solo por donde definiste; (2) preparar **recursos REST** acotados
> (`endpoint` + `params_permitidos`) que ya devuelvan exactamente la información deseada.

---

### 🎙️ Consulta por voz

**Endpoint:** `POST /api/v1/consultas/voz` (multipart/form-data)

Recibe audio, lo transcribe (STT) y lo procesa como una consulta normal
(NL→SQL/API, solo lectura), devolviendo el **objeto estructurado** + un **resumen
hablado** opcional. Reutiliza la misma configuración de voz que `/api/v1/voz`.

**Campos (form-data):**
- `file` (archivo, required): audio `webm/wav/mp3/ogg/m4a`.
- `origen` (string, required): clave del origen (`cartera_db`, `rh_api`, …).
- `formato` (string, opcional): fuerza `texto | tabla | grafico`.
- `responder_voz` (bool, opcional, default `true`): incluir resumen en audio.
- `usuario` (string, opcional): nombre de quien consulta, para personalizar la respuesta.
- `objetivo` (string, opcional): tabla/recurso específico a consultar (omite el matcher).

**Requisitos:** `VOICE_ENABLED=true` y `CONSULTAS_ENABLED=true`.

```bash
curl -X POST "https://bots.tech-energy.lat/api/v1/consultas/voz" \
  -F "file=@pregunta.webm" \
  -F "origen=cartera_db" \
  -F "usuario=Óscar" \
  -F "responder_voz=true"
```

**Respuesta (`ConsultaVozResponse`):**
```json
{
  "pregunta_transcrita": "cuántos clientes hay por sector",
  "resultado": {
    "origen": "cartera_db",
    "tipo": "tabla",
    "titulo": "Cantidad de clientes por sector",
    "texto": "Óscar, aquí tienes el resultado: 6 registro(s).",
    "tabla": { "columnas": ["sector", "cantidad"], "filas": [["Oil & Gas", 20]], "total_filas": 6, "truncado": false },
    "grafico": null,
    "meta": { "origen_tipo": "sql_mysql", "consulta_generada": "SELECT sector, COUNT(*) AS cantidad FROM clientes GROUP BY sector ORDER BY cantidad DESC LIMIT 500", "candidatos": ["clientes"], "advertencias": [] },
    "tiempo_respuesta": 2.3
  },
  "audio_base64": "UklGRiQAAABXQVZF...(resumen hablado en WAV)..."
}
```

> El audio **no dicta las filas** (sería enorme): lee una frase corta y personalizada
> (`resultado.texto`), p.ej. *"Óscar, aquí tienes el resultado: 6 registros."* Para
> tipo=`texto` (un dato puntual) sí lee la respuesta real. La tabla/gráfico se pintan
> desde el objeto `resultado`.

**Códigos:** `503` voz o consultas deshabilitado / faltan dependencias; `413` audio
muy grande; `422` audio vacío/ininteligible; `400` origen/consulta/SQL inválido.

---

### 2. Health del módulo de consultas

**Endpoint:** `GET /api/v1/consultas/health`

```json
{
  "consultas_enabled": true,
  "rules_cargado": true,
  "rules_path": "config/rules.yaml",
  "total_origenes": 2,
  "origenes": [
    { "clave": "rh_api", "tipo": "rest_api", "descripcion": "...", "tablas_o_recursos": ["empleados"] },
    { "clave": "ventas_db", "tipo": "sql_mysql", "descripcion": "...", "tablas_o_recursos": ["usuarios", "ordenes"] }
  ],
  "error_rules": null
}
```

**Códigos:** `400` origen inexistente / consulta inválida / SQL no permitido;
`503` módulo deshabilitado o error de conexión con el origen.

> **Tipos de salida:** `texto` (dato/resumen), `tabla` (`columnas`+`filas`),
> `grafico` (`tipo_grafico`+`etiquetas`+`series`, Fase 2). La agregación para gráficos
> sobre REST se calcula en el servidor (`conteo`/`suma`); sobre SQL la hace la propia BD.

---

## 📋 Esquemas de Datos Completos

### DocumentoPaperless

```json
{
  "id": 1,
  "title": "Código de Ética y Conducta",
  "created": "2026-03-10",
  "modified": "2026-03-11T10:30:00Z",
  "content": null,
  "archive_serial_number": null,
  "correspondent": null,
  "document_type": 1,
  "tags": [1, 2, 3],
  "download_url": "https://paperless.tech-energy.lat/api/documents/1/download/?token=abc123",
  "preview_url": "https://paperless.tech-energy.lat/api/documents/1/preview/?token=abc123",
  "thumbnail_url": "https://paperless.tech-energy.lat/api/documents/1/thumb/?token=abc123"
}
```

**Nuevos campos de URLs:**
- `download_url`: URL para descargar el archivo original
- `preview_url`: URL para visualizar el documento en navegador
- `thumbnail_url`: URL de miniatura del documento

### DocumentoInfo (Chunk)

```json
{
  "doc_id": "3",
  "title": "Código de Ética",
  "chunk_index": 5,
  "total_chunks": 20,
  "created": "2026-03-10",
  "preview": "La integridad se define como...",
  "score": 0.92
}
```

### HealthResponse

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-17T18:41:56.996279",
  "ia_disponible": true,
  "chromadb_disponible": true,
  "paperless_conectado": true,
  "total_documentos": 2
}
```

---

## 🔄 Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Éxito - Operación completada correctamente |
| 400 | Bad Request - Parámetros inválidos o faltantes |
| 422 | Unprocessable Entity - Validación de datos falló |
| 500 | Internal Server Error - Error en el servidor |
| 503 | Service Unavailable - Servicio no disponible (ej: Paperless offline) |

---

## 🌐 Ejemplos de Integración

### Python

```python
import requests

BASE_URL = "https://bots.tech-energy.lat"

# Health check
response = requests.get(f"{BASE_URL}/api/v1/bot-simple/health")
print(response.json())

# Listar documentos
response = requests.get(f"{BASE_URL}/api/v1/bot-simple/documents?limite=5")
documentos = response.json()
print(f"Total documentos: {documentos['total']}")

# Consulta al bot
payload = {
    "pregunta": "¿Qué dice el código de ética sobre integridad?"
}
response = requests.post(
    f"{BASE_URL}/api/v1/bot-simple/query",
    json=payload
)
resultado = response.json()
print(f"Respuesta: {resultado['respuesta']}")
print(f"Tiempo: {resultado['tiempo_respuesta']}s")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'https://bots.tech-energy.lat';

// Health check
async function checkHealth() {
  const response = await axios.get(`${BASE_URL}/api/v1/bot-simple/health`);
  console.log(response.data);
}

// Listar documentos
async function listarDocumentos() {
  const response = await axios.get(`${BASE_URL}/api/v1/bot-simple/documents?limite=5`);
  console.log(`Total documentos: ${response.data.total}`);
  console.log(response.data.documentos);
}

// Consulta al bot
async function consultarBot() {
  const payload = {
    pregunta: "¿Qué dice el código de ética sobre integridad?"
  };
  
  const response = await axios.post(
    `${BASE_URL}/api/v1/bot-simple/query`,
    payload
  );
  
  console.log(`Respuesta: ${response.data.respuesta}`);
  console.log(`Tiempo: ${response.data.tiempo_respuesta}s`);
}

checkHealth();
listarDocumentos();
consultarBot();
```

### PHP

```php
<?php

$BASE_URL = "https://bots.tech-energy.lat";

// Health check
$response = file_get_contents("$BASE_URL/api/v1/bot-simple/health");
$data = json_decode($response, true);
print_r($data);

// Listar documentos
$response = file_get_contents("$BASE_URL/api/v1/bot-simple/documents?limite=5");
$documentos = json_decode($response, true);
echo "Total documentos: " . $documentos['total'] . "\n";

// Consulta al bot
$payload = json_encode([
    "pregunta" => "¿Qué dice el código de ética sobre integridad?"
]);

$options = [
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => $payload
    ]
];

$context = stream_context_create($options);
$response = file_get_contents("$BASE_URL/api/v1/bot-simple/query", false, $context);
$resultado = json_decode($response, true);

echo "Respuesta: " . $resultado['respuesta'] . "\n";
echo "Tiempo: " . $resultado['tiempo_respuesta'] . "s\n";
?>
```

---

## 📝 Notas Importantes

### Límites y Performance

- **Tiempo de respuesta típico**: 0.5-5 segundos (varía según complejidad)
- **Límite de documentos**: 100 documentos por request (ajustable con parámetro `limite`)
- **Timeout**: 300 segundos para operaciones largas (razonamiento profundo, reindexación)

### Costos de IA

Los endpoints que usan IA (query, consulta-rapida, razonamiento-profundo) consumen tokens:
- **Bot Simple**: Usa Ollama local (sin costo)
- **Bot Avanzado**: Puede usar OpenAI (tiene costo)
  - Consulta rápida: ~$0.0001-0.0003 USD
  - Razonamiento profundo: ~$0.0005-0.002 USD

### Dependencias Externas

La API depende de:
- **Paperless-ngx**: Para obtener documentos
- **ChromaDB**: Para búsqueda semántica
- **Ollama/OpenAI**: Para generación de respuestas

Si algún servicio está caído, los endpoints afectados retornarán error 503.

---

## 📎 Uso de URLs de Documentos en Frontend

Los endpoints de documentos ahora incluyen URLs listas para usar en aplicaciones frontend **con autenticación integrada**.

### Campos de URL Disponibles

Cada objeto `DocumentoPaperless` incluye:
- **`download_url`**: Descarga directa del archivo original
- **`preview_url`**: Vista previa del documento (PDF renderizado)
- **`thumbnail_url`**: Miniatura para listas o galerías

### ✅ Autenticación Incluida

**Las URLs ya contienen el token de autenticación** como query parameter (`?token=XXX`), por lo que:

- ✅ Puedes usarlas directamente en `<img>`, `<iframe>`, o `<a>` sin configuración adicional
- ✅ No necesitas agregar headers custom en JavaScript
- ✅ Funcionan inmediatamente al abrirse en el navegador
- ⚠️ **Importante**: No compartas estas URLs públicamente (contienen tu token de acceso)

Ejemplo de URL generada:
```
https://paperless.tech-energy.lat/api/documents/1/preview/?token=abc123def456
                                                           ^^^^^^^^^^^^^^^^^^^
                                                           Token incluido automáticamente
```

### Ejemplos de Uso

#### 1. Mostrar Miniaturas en una Lista

```html
<div class="document-list">
  <!-- Para cada documento -->
  <div class="document-card">
    <img 
      src="${documento.thumbnail_url}" 
      alt="${documento.title}"
      onerror="this.src='/placeholder.png'"
    />
    <h3>${documento.title}</h3>
  </div>
</div>
```

**✅ Funciona directamente - el token ya está en la URL**

#### 2. Botón de Descarga Directo

```html
<a href="${documento.download_url}" download="${documento.title}">
  <button>📥 Descargar Documento</button>
</a>
```

**✅ Sin JavaScript necesario - funciona como un link normal**

#### 3. Preview en Modal/Iframe

```html
<div class="modal">
  <iframe 
    src="${documento.preview_url}" 
    style="width: 100%; height: 600px;"
    title="Vista previa del documento"
  ></iframe>
</div>
```

**✅ El iframe carga directamente sin configuración adicional**

#### 4. React Component Simplificado

```jsx
function DocumentCard({ documento }) {
  const [showPreview, setShowPreview] = useState(false);
  
  return (
    <div className="card">
      <img src={documento.thumbnail_url} alt={documento.title} />
      <h3>{documento.title}</h3>
      
      <button onClick={() => setShowPreview(true)}>
        👁️ Ver Preview
      </button>
      
      <a href={documento.download_url} download>
        📥 Descargar
      </a>
      
      {showPreview && (
        <div className="modal">
          <iframe src={documento.preview_url} />
          <button onClick={() => setShowPreview(false)}>Cerrar</button>
        </div>
      )}
    </div>
  );
}
```

**✅ Sin necesidad de fetch() ni manejo de blobs**

### Manejo de Errores

```javascript
// Verificar si las URLs están disponibles
if (documento.download_url) {
  // URL disponible y lista para usar
  console.log('Documento disponible para descarga');
} else {
  // PAPERLESS_URL o PAPERLESS_TOKEN no configurado
  console.warn('URL de documento no disponible - configuración incompleta');
}

// Manejo de errores de carga de imagen
<img 
  src={documento.thumbnail_url}
  onError={(e) => {
    e.target.src = '/placeholder.png';
    console.error('Error cargando miniatura');
  }}
/>
```

### Consideraciones de Seguridad

1. **URLs Privadas**: Las URLs contienen el token de autenticación - **no las expongas en repositorios públicos o logs**
2. **HTTPS**: Siempre usa HTTPS en producción para proteger el token en tránsito
3. **Rotación de Token**: Si cambias el `PAPERLESS_TOKEN`, todas las URLs anteriores dejarán de funcionar
4. **Caducidad**: Las URLs son válidas mientras el token esté activo (Paperless no caduca tokens por defecto)
5. **Compartir**: Si necesitas compartir un documento, considera crear un endpoint proxy en tu backend que valide permisos

### Ventajas del Enfoque Actual

✅ **Simplicidad**: No necesitas manejar autenticación en el frontend  
✅ **Compatibilidad**: Funciona con cualquier elemento HTML (`<img>`, `<iframe>`, `<a>`)  
✅ **Performance**: El navegador puede cachear las imágenes/documentos automáticamente  
✅ **Less Code**: No necesitas fetch(), blobs, ni manejo manual de headers

### Consideraciones Técnicas

1. **CORS**: No es necesario configurar CORS si usas las URLs directamente en HTML
2. **Caché del Navegador**: Las URLs con query parameters se cachean - considera esto para documentos que cambian frecuentemente
3. **Tamaño de URLs**: Los tokens pueden ser largos - verifica límites si usas URLs en bases de datos
4. **Logging**: Ten cuidado con logs que puedan exponer las URLs completas (con token)

---

## 🆘 Soporte

Para reportar problemas o solicitar ayuda:
- **Documentación Swagger**: https://bots.tech-energy.lat/docs
- **Health Check**: https://bots.tech-energy.lat/api/v1/bot-simple/health

---

**Versión de Documentación:** 1.0.0  
**Última Actualización:** 2026-03-17  
**Servidor de Producción:** bots.tech-energy.lat
