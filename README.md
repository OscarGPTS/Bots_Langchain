# 🤖 API REST - Bots de Documentos con LangChain

API REST construida con **FastAPI** para consultas inteligentes de documentos usando **LangChain**, **ChromaDB**, **OpenAI** y **Ollama**.

---

## 📋 Tabla de Contenidos

- [Inicio Rápido](#-inicio-rápido-5-minutos)
- [Características](#-características)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Cómo Ejecutar](#-cómo-ejecutar)
- [Validar Funcionamiento](#-validar-funcionamiento)
- [Ejemplos de Uso](#-ejemplos-de-uso)
- [Despliegue en Producción](#-despliegue-en-producción-nginx)
- [Solución de Problemas](#-solución-de-problemas)
- [Comandos Útiles](#️-comandos-útiles)

---

## 🚀 Inicio Rápido (5 minutos)

```bash
# 1. Activar entorno virtual
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env
# Editar .env con tus valores (ver sección Configuración)

# 4. Ejecutar API
python scripts/iniciar_api.py

# 5. Abrir documentación
# http://localhost:8000/docs
```

**Acceder a:**
- 🌐 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- ❤️ **Health Check**: http://localhost:8000/health

---

## ✨ Características

### 🌐 API REST
- **FastAPI 0.135.1**: Framework moderno, rápido y con documentación automática
- **Swagger UI**: Documentación interactiva con "Try it out"
- **Pydantic**: Validación automática con esquemas y ejemplos
- **Health checks**: Monitoreo de servicios por componente
- **Singleton pattern**: Bots se inicializan una sola vez (eficiente)
- **CORS**: Configurado y listo
- **Logging**: Tracking de requests con tiempos (header `X-Process-Time`)

### 🤖 Bots Inteligentes

**Bot Simple** (`/api/v1/bot-simple`)
- 🗄️ ChromaDB local + Ollama (phi4-mini:latest)
- ⚡ Búsqueda vectorial sin costos de API
- 📄 87 vectores indexados
- 🔍 4 endpoints: query, analyze-document, recent-documents, health

**Bot Avanzado** (`/api/v1/bot-avanzado`)
- ☁️ ChromaDB + OpenAI (gpt-5-nano)
- 🧠 Modo rápido: 3 chunks, respuestas directas
- 🤔 Modo razonamiento: 10-20 chunks, análisis profundo
- 🔎 Búsqueda semántica pura (sin LLM)
- 📊 116 vectores, estadísticas, reindexación
- 💰 Monitor de costos y tokens
- 📈 6 endpoints completos

### 🛠️ Stack Tecnológico
- **API**: FastAPI + Uvicorn + Gunicorn (producción)
- **IA Local**: Ollama (phi4-mini:latest) - 0 costos
- **IA Cloud**: OpenAI (gpt-5-nano)
- **Vectorización**: ChromaDB persistente
- **Validación**: Pydantic 2.12.5
- **Documentos**: Paperless-ngx con OCR
- **Búsqueda**: LangChain con embeddings semánticos
- **Proxy**: Nginx + SSL/HTTPS (producción)

---

## 🏗️ Instalación

### Requisitos Previos
- Python 3.11+ instalado
- Git instalado
- Acceso a Paperless-ngx
- Ollama o clave de OpenAI

### Pasos de Instalación

```bash
# 1. Clonar repositorio (si aplica)
git clone <repo-url>
cd langchain

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Verificar instalación
python scripts/test_api_imports.py
```

---

## ⚙️ Configuración

### Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto:

```env
# ===== Paperless-ngx =====
PAPERLESS_URL=https://paperless.tudominio.com
PAPERLESS_TOKEN=tu_token_aqui

# ===== Ollama (Local) =====
OLLAMA_URL=https://ollama.tudominio.com
OLLAMA_MODEL=phi4-mini:latest

# ===== OpenAI (Cloud - Opcional) =====
LOCALIA=false  # true = Ollama, false = OpenAI
OPENAI_API_KEY=sk-...

# ===== ChromaDB =====
CHROMA_DB_PATH=./chroma_db
```

### Obtener Token de Paperless

```bash
python scripts/generar_token_paperless.py
```

### Verificar Conexiones

```bash
# Probar Paperless
python scripts/probar_paperless.py

# Ver modelos Ollama
python utils/verificar_ollama.py
```

---

## 📁 Estructura del Proyecto

```
langchain/
├── api/                        # 🌐 API REST
│   ├── main.py                 #    App FastAPI principal
│   ├── dependencies.py         #    Singletons de bots
│   ├── models/
│   │   └── schemas.py          #    Modelos Pydantic
│   └── routes/
│       ├── bot_simple.py       #    4 endpoints bot simple
│       └── bot_avanzado.py     #    6 endpoints bot avanzado
├── bot_documentos.py           # 🤖 Bot Simple (Ollama)
├── bot_documentos_avanzado.py  # 🚀 Bot Avanzado (OpenAI)
├── scripts/
│   ├── iniciar_api.py          # ▶️ Iniciar API
│   ├── test_api_cliente.py     # 🧪 Tests completos
│   └── test_api_imports.py     # ✅ Validar imports
├── chroma_db/                  # 📊 Base de datos vectorial
├── .env                        # 🔐 Configuración (crear)
└── requirements.txt            # 📦 Dependencias
```

---

## 🎯 Endpoints de la API

### **General**
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| GET | `/health` | Health check global |

### **Bot Simple** - `/api/v1/bot-simple`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/query` | Consulta general |
| POST | `/analyze-document` | Analizar documento por ID |
| GET | `/recent-documents` | Documentos recientes de Paperless |
| GET | `/health` | Health check del bot |

**Ejemplo Request:**
```json
{
  "pregunta": "¿Qué dice el código de ética sobre integridad?"
}
```

**Ejemplo Response:**
```json
{
  "respuesta": "El código de ética define...",
  "tiempo_respuesta": 2.5
}
```

### **Bot Avanzado** - `/api/v1/bot-avanzado`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/consulta-rapida` | Respuesta rápida (3 chunks) |
| POST | `/razonamiento-profundo` | Análisis profundo (10-20 chunks) |
| POST | `/busqueda-semantica` | Búsqueda vectorial sin LLM |
| GET | `/stats` | Estadísticas (docs, vectores, costos) |
| POST | `/reindexar` | Forzar reindexación |
| GET | `/health` | Health check del bot |

**Ejemplo Request (Razonamiento):**
```json
{
  "pregunta": "Analiza las políticas de vacaciones",
  "filtros": {"created": "2026"},
  "k": 15
}
```

**Ejemplo Response:**
```json
{
  "respuesta": "Análisis detallado...",
  "chunks_usados": 15,
  "estadisticas": {
    "tokens_total": 1500,
    "costo_usd": 0.00045
  },
  "tiempo_respuesta": 12.3
}
```

---

## ▶️ Cómo Ejecutar

### Desarrollo (con auto-reload)

```bash
# Opción 1: Script simplificado (recomendado)
python scripts/iniciar_api.py

# Opción 2: Uvicorn directo
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Opción 3: Módulo Python
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Producción

```bash
# Con Uvicorn (4 workers)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Con Gunicorn + Uvicorn workers (recomendado)
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```bash
# Build
docker build -t bots-api .

# Run
docker run -d -p 8000:8000 --env-file .env bots-api
```

---

## ✅ Validar Funcionamiento

### 1. Health Check

```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing

# cURL
curl http://localhost:8000/health

# Python
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "timestamp": 1773348021.71,
  "services": {
    "bot_simple": "/api/v1/bot-simple/health",
    "bot_avanzado": "/api/v1/bot-avanzado/health"
  }
}
```

### 2. Test Automatizado

```bash
python scripts/test_api_cliente.py
```

Prueba todos los endpoints:
- ✅ Health checks
- ✅ Consultas al bot simple
- ✅ Consultas avanzadas
- ✅ Búsqueda semántica
- ✅ Estadísticas

### 3. Swagger UI

Abre en tu navegador: **http://localhost:8000/docs**

Usa el botón **"Try it out"** para probar endpoints interactivamente.

---

## 💻 Ejemplos de Uso

### PowerShell

```powershell
# Consulta simple
$body = @{pregunta="¿Cuál es el horario de trabajo?"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/bot-simple/query" `
  -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# Búsqueda semántica
$body = @{query="seguridad e higiene"; k=5} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/bot-avanzado/busqueda-semantica" `
  -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# Estadísticas
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/bot-avanzado/stats" -UseBasicParsing
```

### cURL

```bash
# Consulta simple
curl -X POST "http://localhost:8000/api/v1/bot-simple/query" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué dice el código de ética?"}'

# Razonamiento profundo
curl -X POST "http://localhost:8000/api/v1/bot-avanzado/razonamiento-profundo" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Analiza las políticas de vacaciones", "k": 15}'

# Búsqueda semántica
curl -X POST "http://localhost:8000/api/v1/bot-avanzado/busqueda-semantica" \
  -H "Content-Type: application/json" \
  -d '{"query": "seguridad e higiene", "k": 5}'

# Estadísticas
curl "http://localhost:8000/api/v1/bot-avanzado/stats"
```

### Python

```python
import requests

# Consulta al bot simple
response = requests.post(
    "http://localhost:8000/api/v1/bot-simple/query",
    json={"pregunta": "¿Qué dice el código de ética?"}
)
data = response.json()
print(data["respuesta"])
print(f"Tiempo: {data['tiempo_respuesta']}s")

# Razonamiento profundo con filtros
response = requests.post(
    "http://localhost:8000/api/v1/bot-avanzado/razonamiento-profundo",
    json={
        "pregunta": "Analiza las políticas de vacaciones",
        "filtros": {"created": "2026"},
        "k": 15
    }
)
data = response.json()
print(data["respuesta"])
if data["estadisticas"]:
    print(f"Tokens: {data['estadisticas']['tokens_total']}")
    print(f"Costo: ${data['estadisticas']['costo_usd']:.6f}")

# Búsqueda semántica
response = requests.post(
    "http://localhost:8000/api/v1/bot-avanzado/busqueda-semantica",
    json={"query": "seguridad e higiene", "k": 5}
)
for doc in response.json()["resultados"]:
    print(f"- {doc['title']} (score: {doc['score']:.4f})")
    print(f"  {doc['preview'][:100]}...")

# Estadísticas
response = requests.get("http://localhost:8000/api/v1/bot-avanzado/stats")
stats = response.json()
print(f"Documentos: {stats['documentos_totales']}")
print(f"Vectores: {stats['vectores']}")
print(f"Modo: {stats['modo']}")
```

### JavaScript

```javascript
// Consulta simple
const response = await fetch('http://localhost:8000/api/v1/bot-simple/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({pregunta: '¿Qué dice el código de ética?'})
});
const data = await response.json();
console.log(data.respuesta);

// Búsqueda semántica
const response2 = await fetch('http://localhost:8000/api/v1/bot-avanzado/busqueda-semantica', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'seguridad e higiene', k: 5})
});
const results = await response2.json();
results.resultados.forEach(doc => {
  console.log(`- ${doc.title} (score: ${doc.score.toFixed(4)})`);
});
```

---

## 🌐 Despliegue en Producción (Nginx)

### 1. Configuración de Nginx

Crear `/etc/nginx/sites-available/bots-api`:

```nginx
server {
    listen 80;
    server_name api.tudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.tudominio.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tudominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Logs
    access_log /var/log/nginx/bots-api-access.log;
    error_log /var/log/nginx/bots-api-error.log;

    # Límite de request
    client_max_body_size 50M;

    # Proxy a FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para consultas largas
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Activar Sitio

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/bots-api /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### 3. Servicio Systemd

Crear `/etc/systemd/system/bots-api.service`:

```ini
[Unit]
Description=Bots API - FastAPI con Uvicorn
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/app/langchain
Environment="PATH=/app/langchain/.venv/bin"
ExecStart=/app/langchain/.venv/bin/gunicorn api.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/bots-api/access.log \
    --error-logfile /var/log/bots-api/error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Iniciar Servicio

```bash
# Crear logs
sudo mkdir -p /var/log/bots-api
sudo chown www-data:www-data /var/log/bots-api

# Activar servicio
sudo systemctl daemon-reload
sudo systemctl start bots-api
sudo systemctl enable bots-api

# Verificar status
sudo systemctl status bots-api
```

### 5. SSL con Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d api.tudominio.com

# Auto-renewal ya configurado
sudo certbot renew --dry-run
```

### 6. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

---

## 🔧 Solución de Problemas

### Puerto 8000 ocupado

```powershell
# Ver qué proceso usa el puerto
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object {
    Get-Process -Id $_.OwningProcess
}

# Detener proceso
Stop-Process -Id <PID> -Force

# O detener todos los Python
Get-Process python | Stop-Process -Force
```

### Servidor no responde

1. **Verificar que está corriendo:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Revisar logs de inicio:**
   Espera a ver `✅ API lista para recibir peticiones`

3. **Error de Ollama (normal):**
   ```
   ⚠️ Error indexando documento: ... timeout 524
   ```
   - Servidor remoto de Ollama sobrecargado
   - API **continúa funcionando** de todos modos
   - Solo afecta bot simple si Ollama es necesario

### ModuleNotFoundError

```bash
# Activar entorno virtual
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux

# Reinstalar dependencias
pip install -r requirements.txt
```

### ChromaDB corrupto

```bash
# Detener servidor (CTRL+C)

# Eliminar ChromaDB
Remove-Item -Path "chroma_db" -Recurse -Force  # Windows
rm -rf chroma_db  # Linux

# Reiniciar (recreará ChromaDB automáticamente)
python scripts/iniciar_api.py
```

### Swagger UI no carga

1. **Limpiar caché:** CTRL + Shift + R
2. **Probar ReDoc:** http://localhost:8000/redoc
3. **Verificar servidor:** `curl http://localhost:8000/health`

---

## 🛠️ Comandos Útiles

### Gestión del Servidor

```bash
# Iniciar
python scripts/iniciar_api.py

# Detener: CTRL+C en la terminal

# Ver procesos
Get-Process python  # Windows
ps aux | grep python  # Linux

# Ver puerto 8000
Get-NetTCPConnection -LocalPort 8000  # Windows
lsof -i :8000  # Linux

# Matar procesos Python
Get-Process python | Stop-Process -Force  # Windows
pkill python  # Linux
```

### Testing

```bash
# Test completo
python scripts/test_api_cliente.py

# Validar imports
python scripts/test_api_imports.py

# Health check
curl http://localhost:8000/health
```

### Diagnóstico

```bash
# Ver logs (si systemd)
sudo journalctl -u bots-api -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/bots-api-access.log

# Test de conectividad
Test-NetConnection -ComputerName localhost -Port 8000  # Windows
nc -zv localhost 8000  # Linux
```

### Mantenimiento

```bash
# Reindexar documentos
curl -X POST http://localhost:8000/api/v1/bot-avanzado/reindexar

# Ver estadísticas
curl http://localhost:8000/api/v1/bot-avanzado/stats

# Restart del servicio (producción)
sudo systemctl restart bots-api
```

---

## 📊 Tiempos de Inicialización

**Primera vez (esperado):**
- Bot Simple: 5-15 segundos
- Bot Avanzado: 10-30 segundos  
- **Total: 15-45 segundos**

El servidor carga:
- ✅ Modelos de IA (Ollama/OpenAI)
- ✅ ChromaDB persistente
- ✅ Conexión con Paperless
- ✅ Indexación de documentos (si es necesario)

**Mensaje de éxito:**
```
✅ API lista para recibir peticiones
📚 Documentación: http://localhost:8000/docs
INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## 🔐 Seguridad (Producción)

**Antes de producción, implementar:**

1. ✅ **Autenticación** (JWT o API Keys)
2. ✅ **Rate limiting** (slowapi)
3. ✅ **CORS restrictivo** (solo dominios permitidos)
4. ✅ **HTTPS obligatorio** (Let's Encrypt)
5. ✅ **Validación robusta** (ya incluido con Pydantic)
6. ✅ **Logs detallados**
7. ✅ **Firewall** (UFW en Linux)
8. ✅ **Monitoreo** (Prometheus + Grafana)

---

## 📄 Licencia

Proyecto interno - GPT Services

---

## 💡 Tips

- **Siempre activa el entorno virtual** antes de ejecutar comandos
- **Espera pacientemente** la primera inicialización (30-45 seg)
- **Revisa los logs** para entender qué está pasando
- **Usa Swagger UI** para probar endpoints interactivamente
- **El error 524 de Ollama es ignorable**, el servidor continúa
- **ChromaDB se recrea automáticamente** si se elimina

---

## 🎯 Próximos Pasos

1. ✅ **Ejecutar**: `python scripts/iniciar_api.py`
2. ✅ **Validar**: `python scripts/test_api_cliente.py`
3. ✅ **Explorar**: http://localhost:8000/docs
4. 🚀 **Desplegar**: Configurar Nginx + systemd (ver arriba)
5. 🔒 **Securizar**: Implementar autenticación y rate limiting

---

¡Tu API está lista para usar! 🎉

**Documentación interactiva:** http://localhost:8000/docs
