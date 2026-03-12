# 🚀 Inicio Rápido - API de Bots

## ⚡ Instalación Express (5 minutos)

### 1️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2️⃣ Verificar configuración
Asegúrate de tener el archivo `.env` configurado:
```env
PAPERLESS_URL=https://paperless.example.com
PAPERLESS_TOKEN=tu_token
OLLAMA_URL=https://ollama.example.com
OLLAMA_MODEL=phi4-mini:latest
LOCALIA=true
```

### 3️⃣ Iniciar la API
```bash
python scripts/iniciar_api.py
```

### 4️⃣ Abrir documentación
Abre en tu navegador: **http://localhost:8000/docs**

---

## 📝 Primer Request

### Usando cURL:
```bash
curl -X POST "http://localhost:8000/api/v1/bot-simple/query" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué dice el código de ética?"}'
```

### Usando Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/bot-simple/query",
    json={"pregunta": "¿Qué dice el código de ética?"}
)

print(response.json())
```

### Usando la documentación interactiva:
1. Ve a http://localhost:8000/docs
2. Haz clic en `/api/v1/bot-simple/query`
3. Haz clic en "Try it out"
4. Escribe tu pregunta
5. Haz clic en "Execute"

---

## 🎯 Endpoints Principales

### Bot Simple (consultas rápidas)
- `POST /api/v1/bot-simple/query` - Consulta general
- `GET /api/v1/bot-simple/health` - Estado del servicio

### Bot Avanzado (análisis profundo)
- `POST /api/v1/bot-avanzado/consulta-rapida` - Consulta con 3 chunks
- `POST /api/v1/bot-avanzado/razonamiento-profundo` - Análisis con 10-20 chunks
- `POST /api/v1/bot-avanzado/busqueda-semantica` - Solo búsqueda vectorial
- `GET /api/v1/bot-avanzado/stats` - Estadísticas de uso

---

## 📚 Documentación Completa

Lee la documentación completa en: [API_DOCS.md](./API_DOCS.md)

---

## 🐛 Problemas Comunes

### ❌ "Error: Port already in use"
Otro proceso está usando el puerto 8000:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### ❌ "Error: ChromaDB not available"
```bash
# Verifica que exista la carpeta
ls chroma_db

# Si no existe, ejecuta
python scripts/indexar_docs_simple.py
```

### ❌ "Error: Ollama not available"
```bash
# Verifica que Ollama esté corriendo
curl http://ollama-url/api/tags
```

---

## 🔧 Modos de Ejecución

### Desarrollo (con auto-reload):
```bash
python scripts/iniciar_api.py
```

### Producción (sin auto-reload):
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Con múltiples workers:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 💡 Tips

1. **Documentación interactiva**: http://localhost:8000/docs (Swagger UI)
2. **Documentación alternativa**: http://localhost:8000/redoc (ReDoc)
3. **Health check**: http://localhost:8000/health
4. **Ver logs**: Los logs aparecen en la terminal donde iniciaste la API
5. **Detener servidor**: Presiona `Ctrl+C` en la terminal

---

## 🎉 ¡Listo!

Tu API está corriendo y lista para recibir peticiones. Ve a la documentación interactiva para probar todos los endpoints.
