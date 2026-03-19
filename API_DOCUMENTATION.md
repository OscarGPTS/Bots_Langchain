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

⚠️ **Importante**: Estas URLs requieren autenticación con el token de Paperless. En el frontend, debes incluir el header:
```javascript
headers: {
  'Authorization': 'Token YOUR_PAPERLESS_TOKEN'
}
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
  "download_url": "https://paperless.tech-energy.lat/api/documents/1/download/",
  "preview_url": "https://paperless.tech-energy.lat/api/documents/1/preview/",
  "thumbnail_url": "https://paperless.tech-energy.lat/api/documents/1/thumb/"
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

Los endpoints de documentos ahora incluyen URLs listas para usar en aplicaciones frontend:

### Campos de URL Disponibles

Cada objeto `DocumentoPaperless` incluye:
- **`download_url`**: Descarga directa del archivo original
- **`preview_url`**: Vista previa del documento (PDF renderizado)
- **`thumbnail_url`**: Miniatura para listas o galerías

### Autenticación Requerida

**Importante**: Todas las URLs requieren el header de autenticación de Paperless:

```javascript
Authorization: Token YOUR_PAPERLESS_TOKEN
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

#### 2. Botón de Descarga con Fetch

```javascript
async function descargarDocumento(downloadUrl, filename) {
  const response = await fetch(downloadUrl, {
    headers: {
      'Authorization': `Token ${PAPERLESS_TOKEN}`
    }
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

#### 3. Preview en Modal/Iframe

```html
<div class="modal">
  <iframe 
    id="document-preview"
    src="" 
    style="width: 100%; height: 600px;"
  ></iframe>
</div>

<script>
function mostrarPreview(previewUrl) {
  // Nota: iframes tienen limitaciones con headers custom
  // Mejor usar fetch + blob para mayor control
  fetch(previewUrl, {
    headers: { 'Authorization': `Token ${PAPERLESS_TOKEN}` }
  })
  .then(res => res.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    document.getElementById('document-preview').src = url;
  });
}
</script>
```

#### 4. React Component Ejemplo

```jsx
function DocumentCard({ documento }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  
  const loadPreview = async () => {
    const response = await fetch(documento.preview_url, {
      headers: { 'Authorization': `Token ${process.env.PAPERLESS_TOKEN}` }
    });
    const blob = await response.blob();
    setPreviewUrl(URL.createObjectURL(blob));
  };
  
  return (
    <div className="card">
      <img src={documento.thumbnail_url} alt={documento.title} />
      <h3>{documento.title}</h3>
      <button onClick={loadPreview}>Ver Preview</button>
      <a href={documento.download_url} download>Descargar</a>
      
      {previewUrl && <iframe src={previewUrl} />}
    </div>
  );
}
```

### Manejo de Errores

```javascript
// Verificar si las URLs están disponibles
if (documento.download_url) {
  // URL disponible - mostrar botón de descarga
} else {
  // PAPERLESS_URL no configurado o documento sin ID
  console.warn('URL de documento no disponible');
}
```

### Consideraciones

1. **CORS**: Asegúrate de que Paperless-ngx tenga CORS configurado para tu dominio frontend
2. **Seguridad**: Nunca expongas el `PAPERLESS_TOKEN` en el frontend - usa un proxy backend
3. **Performance**: Las miniaturas son más ligeras que previews completos - úsalas en listas
4. **Caché**: Considera cachear blobs de documentos para evitar descargas repetidas

---

## 🆘 Soporte

Para reportar problemas o solicitar ayuda:
- **Documentación Swagger**: https://bots.tech-energy.lat/docs
- **Health Check**: https://bots.tech-energy.lat/api/v1/bot-simple/health

---

**Versión de Documentación:** 1.0.0  
**Última Actualización:** 2026-03-17  
**Servidor de Producción:** bots.tech-energy.lat
