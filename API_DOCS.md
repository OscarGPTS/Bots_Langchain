# 📚 API de Bots de Documentos - Documentación

API REST construida con **FastAPI** para interactuar con bots inteligentes de búsqueda y análisis de documentos usando LangChain, ChromaDB y modelos de IA (OpenAI/Ollama).

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Asegúrate de tener configurado el archivo `.env` con:

```env
# Paperless
PAPERLESS_URL=https://paperless.example.com
PAPERLESS_TOKEN=tu_token_aqui

# Ollama (local)
OLLAMA_URL=https://ollama.example.com
OLLAMA_MODEL=phi4-mini:latest

# OpenAI (opcional)
LOCALIA=true  # true = Ollama, false = OpenAI
OPENAI_API_KEY=sk-...

# ChromaDB
CHROMA_DB_PATH=./chroma_db
```

### 3. Iniciar el servidor

```bash
python scripts/iniciar_api.py
```

O directamente con uvicorn:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acceder a la documentación

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📋 Endpoints Disponibles

### **General**

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Health check global |

---

### **Bot Simple** (`/api/v1/bot-simple`)

Bot básico con búsqueda semántica usando ChromaDB y Ollama local.

#### **POST** `/api/v1/bot-simple/query`
Realizar consulta general.

**Request:**
```json
{
  "pregunta": "¿Qué dice el código de ética sobre integridad?"
}
```

**Response:**
```json
{
  "respuesta": "El código de ética define la integridad como...",
  "tiempo_respuesta": 2.5
}
```

#### **POST** `/api/v1/bot-simple/analyze-document`
Analizar documento específico por ID.

**Request:**
```json
{
  "documento_id": 1,
  "pregunta": "¿Cuáles son los puntos clave?"
}
```

**Response:**
```json
{
  "respuesta": "Los puntos clave son: 1)...",
  "tiempo_respuesta": 3.2
}
```

####  **GET** `/api/v1/bot-simple/recent-documents`
Listar documentos recientes.

**Response:**
```json
{
  "respuesta": "📚 Últimos 10 documentos:\n1. Código de Ética...",
  "tiempo_respuesta": 0.5
}
```

#### **GET** `/api/v1/bot-simple/health`
Health check del bot simple.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-12T10:30:00",
  "ia_disponible": true,
  "chromadb_disponible": true,
  "paperless_conectado": true,
  "total_documentos": 58
}
```

---

### **Bot Avanzado** (`/api/v1/bot-avanzado`)

Bot avanzado con análisis profundo, razonamiento complejo y soporte dual (OpenAI/Ollama).

#### **POST** `/api/v1/bot-avanzado/consulta-rapida`
Consulta rápida con 3 chunks relevantes.

**Request:**
```json
{
  "pregunta": "¿Cuál es el horario de trabajo?",
  "filtros": {
    "created": "2026"
  }
}
```

**Response:**
```json
{
  "respuesta": "El horario de trabajo es...",
  "estadisticas": {
    "tokens_entrada": 150,
    "tokens_salida": 80,
    "costo_usd": 0.00015
  },
  "tiempo_respuesta": 3.2
}
```

#### **POST** `/api/v1/bot-avanzado/razonamiento-profundo`
Análisis profundo con hasta 20 chunks.

**Request:**
```json
{
  "pregunta": "Analiza las políticas de vacaciones y compáralas con la ley",
  "filtros": null,
  "k": 10
}
```

**Response:**
```json
{
  "respuesta": "Análisis detallado:\n1. Políticas internas...",
  "estadisticas": {
    "tokens_entrada": 1200,
    "tokens_salida": 450,
    "costo_usd": 0.00245
  },
  "tiempo_respuesta": 8.5
}
```

#### **POST** `/api/v1/bot-avanzado/busqueda-semantica`
Búsqueda vectorial sin generar respuesta.

**Request:**
```json
{
  "query": "políticas de seguridad",
  "k": 5,
  "filtros": null
}
```

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
      "preview": "La seguridad es fundamental para..."
    }
  ],
  "total": 1,
  "tiempo_respuesta": 0.8
}
```

#### **GET** `/api/v1/bot-avanzado/stats`
Estadísticas del bot avanzado.

**Response:**
```json
{
  "total_documentos": 3,
  "total_vectores": 116,
  "modo": "cloud (OpenAI)",
  "modelo_rapido": "gpt-4o-mini",
  "modelo_razonamiento": "gpt-4o",
  "documentos_indexados": []
}
```

#### **POST** `/api/v1/bot-avanzado/reindexar`
Forzar reindexación de documentos.

**⚠️ ADVERTENCIA**: Operación costosa, puede tardar varios minutos.

**Response:**
```json
{
  "mensaje": "Reindexación completada",
  "documentos_nuevos": 2,
  "documentos_actualizados": 3,
  "tiempo_total": 45.2
}
```

#### **GET** `/api/v1/bot-avanzado/health`
Health check del bot avanzado.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-12T10:30:00",
  "ia_disponible": true,
  "chromadb_disponible": true,
  "paperless_conectado": true,
  "total_documentos": 116
}
```

---

## 🔧 Configuración

### Filtros de Metadata

Se pueden usar en las consultas avanzadas:

```json
{
  "filtros": {
    "created": "2026",
    "tags": "contrato",
    "title": {"$contains": "ética"}
  }
}
```

### Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `LOCALIA` | Usar Ollama (true) o OpenAI (false) | `true` |
| `OLLAMA_URL` | URL del servidor Ollama | - |
| `OLLAMA_MODEL` | Modelo de Ollama | `phi4-mini:latest` |
| `OPENAI_API_KEY` | API Key de OpenAI | - |
| `OPENAI_MODEL_RAPIDO` | Modelo rápido de OpenAI | `gpt-4o-mini` |
| `OPENAI_MODEL_RAZONAMIENTO` | Modelo con razonamiento | `gpt-4o` |
| `CHROMA_DB_PATH` | Ruta de ChromaDB | `./chroma_db` |
| `CHUNK_SIZE` | Tamaño de chunks | `1000` |
| `CHUNK_OVERLAP` | Overlap de chunks | `150` |

---

## 📝 Ejemplo de Uso (Python)

```python
import requests

BASE_URL = "http://localhost:8000"

# Consulta simple
response = requests.post(
    f"{BASE_URL}/api/v1/bot-simple/query",
    json={"pregunta": "¿Qué dice el código de ética?"}
)
print(response.json())

# Consulta avanzada con filtros
response = requests.post(
    f"{BASE_URL}/api/v1/bot-avanzado/consulta-rapida",
    json={
        "pregunta": "¿Cuál es el horario de trabajo?",
        "filtros": {"created": "2026"}
    }
)
print(response.json())

# Búsqueda semántica
response = requests.post(
    f"{BASE_URL}/api/v1/bot-avanzado/busqueda-semantica",
    json={
        "query": "políticas de seguridad",
        "k": 5
    }
)
print(response.json())
```

---

## 📝 Ejemplo de Uso (cURL)

```bash
# Consulta simple
curl -X POST "http://localhost:8000/api/v1/bot-simple/query" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué dice el código de ética?"}'

# Razonamiento profundo
curl -X POST "http://localhost:8000/api/v1/bot-avanzado/razonamiento-profundo" \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "Analiza las políticas de vacaciones",
    "k": 10
  }'

# Health check
curl "http://localhost:8000/api/v1/bot-avanzado/health"
```

---

## 📝 Ejemplo de Uso (JavaScript/Fetch)

```javascript
// Consulta rápida
const response = await fetch('http://localhost:8000/api/v1/bot-simple/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    pregunta: '¿Qué dice el código de ética sobre integridad?'
  })
});

const data = await response.json();
console.log(data.respuesta);
```

---

## 🏗️ Arquitectura

```
FastAPI Server
│
├── Bot Simple (Ollama + ChromaDB)
│   ├── Búsqueda semántica (5 chunks)
│   ├── Análisis de documentos
│   └── Listado de documentos
│
├── Bot Avanzado (OpenAI/Ollama + ChromaDB)
│   ├── Consulta rápida (3 chunks)
│   ├── Razonamiento profundo (10-20 chunks)
│   ├── Búsqueda semántica
│   └── Reindexación
│
├── ChromaDB (Vectores persistentes)
│   ├── Colección: docs_simple
│   ├── Colección: docs_openai
│   └── Colección: documentos_paperless
│
└── Paperless-ngx (Fuente de documentos)
```

---

## 🔒 Seguridad (Producción)

Para producción, considera implementar:

1. **Autenticación JWT** o **API Keys**
2. **Rate limiting** con `slowapi`
3. **CORS** restrictivo (solo dominios permitidos)
4. **HTTPS** obligatorio
5. **Validación adicional** de inputs
6. **Logging** robusto
7. **Monitoreo** con Prometheus/Grafana

Ejemplo de autenticación básica con API Key:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "tu_clave_secreta_aqui"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Usar en endpoints
@router.post("/query", dependencies=[Depends(verify_api_key)])
async def query(...):
    ...
```

---

## 🐛 Troubleshooting

### Error: "IA no disponible"
- Verifica que Ollama esté corriendo: `curl http://ollama-url/api/tags`
- Verifica el modelo: `ollama list`

### Error: "ChromaDB no disponible"
- Verifica permisos en `./chroma_db`
- Verifica que `langchain-chroma` esté instalado

### Error: "Paperless conectado: false"
- Verifica `PAPERLESS_URL` y `PAPERLESS_TOKEN` en `.env`
- Prueba manualmente: `curl -H "Authorization: Token TOKEN" URL/api/documents/`

### Performance lento
- Reduce `k` en búsquedas semánticas
- Usa consulta rápida en lugar de razonamiento profundo
- Verifica latencia de Ollama/OpenAI
- Considera aumentar recursos del servidor

---

## 📦 Despliegue

### Docker (Recomendado)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t bots-api .
docker run -p 8000:8000 --env-file .env bots-api
```

### Producción con Gunicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📊 Monitoreo y Logs

La API incluye:
- **Logging automático** de todas las peticiones
- **Header `X-Process-Time`** con tiempo de procesamiento
- **Health checks** en `/health`
- **Métricas de uso** en `/api/v1/bot-avanzado/stats`

---

## 🤝 Contribuir

Para agregar nuevos endpoints:

1. Crear schema en `api/models/schemas.py`
2. Agregar ruta en `api/routes/`
3. Actualizar esta documentación

---

## 📄 Licencia

Este proyecto es parte del sistema de gestión de documentos interno.

---

## 📞 Soporte

Para dudas o problemas, contacta al equipo de desarrollo.
