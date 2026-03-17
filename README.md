# 🤖 API REST - Bots de Documentos con LangChain

API REST construida con **FastAPI** para consultas inteligentes de documentos usando **LangChain**, **ChromaDB**, **OpenAI** y **Ollama**.

> ✅ **CONFIGURACIÓN EN PRODUCCIÓN (bots.tech-energy.lat):**
> - **Systemd Service:** `/etc/systemd/system/bots.service` (no `bots-api.service`)
> - **Puerto:** `8001` (evita conflicto con otras apps en puerto 8000)
> - **Nginx:** `/etc/nginx/sites-available/bots.conf`
> - **Usuario:** `tech-energy` con grupo `www-data`
> - Ver [Configuración Real en Producción](#✅-configuración-real-en-producción-botstech-energylat) para detalles exactos

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
- [Despliegue en Producción](#-despliegue-en-producción)
- [Guía Rápida de Despliegue en Producción](#-guía-rápida-de-despliegue-en-producción) ⭐
- [Solución de Problemas](#-solución-de-problemas)
- [Comandos Útiles](#️-comandos-útiles)

---

## 🚀 Inicio Rápido (5 minutos)

### Desarrollo Local

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

> 📋 **Para despliegue en producción (Ubuntu 24.04):** Ver la [Guía Rápida de Despliegue en Producción](#-guía-rápida-de-despliegue-en-producción) con configuración completa para Nginx, Cloudflare Tunnel y Systemd.

**Acceder a:**

**Desarrollo (local):**
- 🌐 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- ❤️ **Health Check**: http://localhost:8000/health

**Producción:**
- 🌐 **Swagger UI**: https://bots.tech-energy.lat/docs
- 📖 **ReDoc**: https://bots.tech-energy.lat/redoc
- ❤️ **Health Check**: https://bots.tech-energy.lat/health
- 🔒 **Autenticación**: Gestionada por Cloudflare Zero Trust

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
- 🔍 5 endpoints: query, analyze-document, documents, recent-documents, health

**Bot Avanzado** (`/api/v1/bot-avanzado`)
- ☁️ ChromaDB + OpenAI (gpt-5-nano)
- 🧠 Modo rápido: 3 chunks, respuestas directas
- 🤔 Modo razonamiento: 10-20 chunks, análisis profundo
- 🔎 Búsqueda semántica pura (sin LLM)
- 📊 116 vectores, estadísticas, reindexación
- 💰 Monitor de costos y tokens
- 📈 8 endpoints completos

### 🛠️ Stack Tecnológico
- **API**: FastAPI + Uvicorn + Gunicorn (producción)
- **IA Local**: Ollama (phi4-mini:latest) - 0 costos
- **IA Cloud**: OpenAI (gpt-5-nano)
- **Vectorización**: ChromaDB persistente
- **Validación**: Pydantic 2.12.5
- **Documentos**: Paperless-ngx con OCR
- **Búsqueda**: LangChain con embeddings semánticos
- **Proxy**: Nginx + Cloudflare Zero Trust (producción)
- **Dominio**: https://bots.tech-energy.lat

---

## 🏗️ Instalación

### Requisitos Previos
- **Python 3.11+** (probado con Python 3.12.3)
- **Git** instalado
- **Acceso a Paperless-ngx**
- **Ollama** (local) o **clave de OpenAI** (cloud)

### Instalación en Ubuntu/Linux

#### 1. Instalar Dependencias del Sistema

**Ubuntu 24.04 / Debian:**
```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar Python y herramientas de desarrollo
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    build-essential \
    pkg-config \
    libsqlite3-dev \
    git \
    curl

# Verificar versión de Python
python3 --version  # Debe mostrar Python 3.12.3
```

**CentOS/RHEL/Rocky Linux:**
```bash
sudo dnf install -y python3.12 python3.12-devel gcc gcc-c++ make sqlite-devel git
```

#### 2. Clonar Repositorio

```bash
git clone <repo-url>
cd langchain
```

#### 3. Crear Entorno Virtual

```bash
# Crear entorno virtual con Python 3.12
python3 -m venv .venv

# Si usas Python 3.12 específicamente:
python3.12 -m venv .venv
```

#### 4. Activar Entorno Virtual

```bash
# Linux/Mac
source .venv/bin/activate

# Verificar que estás en el venv
which python3  # Debe mostrar: /home/usuario/langchain/.venv/bin/python3
```

#### 5. Actualizar pip y Herramientas

```bash
# Actualizar pip a la última versión
pip install --upgrade pip setuptools wheel

# Verificar pip
pip --version
```

#### 6. Instalar Dependencias de Python

```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# Si hay errores con algún paquete específico, instalar primero las dependencias base:
pip install numpy pydantic
pip install -r requirements.txt
```

#### 7. Verificar Instalación

```bash
# Probar imports
python3 scripts/test_api_imports.py

# Verificar conexión con Paperless
python3 scripts/probar_paperless.py
```

### Instalación en Windows

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd langchain

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno
.venv\Scripts\Activate.ps1

# 4. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verificar instalación
python scripts/test_api_imports.py
```

### Solución de Problemas Comunes

#### Error: "No module named '_sqlite3'"
```bash
# Ubuntu/Debian
sudo apt install -y libsqlite3-dev
python3 -m venv .venv --clear  # Recrear venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Error: "error: command 'gcc' failed"
```bash
# Instalar compiladores
sudo apt install -y build-essential python3-dev
```

#### Error: "externally-managed-environment"
```bash
# Asegúrate de estar en el entorno virtual
source .venv/bin/activate
# Si persiste, usa:
pip install --break-system-packages -r requirements.txt  # ⚠️ NO recomendado
```

#### Error al instalar ChromaDB o paquetes con C extensions
```bash
# Instalar dependencias de desarrollo
sudo apt install -y python3.12-dev libsqlite3-dev pkg-config
# Reinstalar
pip install --no-cache-dir chromadb
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
│       ├── bot_simple.py       #    5 endpoints bot simple
│       └── bot_avanzado.py     #    8 endpoints bot avanzado
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
| POST | `/query` | Consulta general con IA |
| POST | `/analyze-document` | Analizar documento específico por ID |
| GET | `/documents` | Listar todos los documentos (JSON) |
| GET | `/recent-documents` | Documentos recientes (JSON) |
| GET | `/health` | Health check del bot |

**Ejemplo Request (POST /query):**
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

**Ejemplo Response (GET /documents):**
```json
{
  "documentos": [
    {
      "id": 3,
      "title": "Reglamento Interno de Trabajo",
      "created": "2026-03-11",
      "modified": "2026-03-11T16:21:45.158706Z",
      "tags": [],
      "document_type": null,
      "correspondent": null,
      "archive_serial_number": null
    }
  ],
  "total": 4,
  "tiempo_respuesta": 0.89
}
```

### **Bot Avanzado** - `/api/v1/bot-avanzado`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/consulta-rapida` | Respuesta rápida (3 chunks) |
| POST | `/razonamiento-profundo` | Análisis profundo (10-20 chunks) |
| POST | `/busqueda-semantica` | Búsqueda vectorial sin LLM |
| GET | `/documents` | Listar todos los documentos (JSON) |
| GET | `/recent-documents` | Documentos recientes (JSON) |
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

**Linux/Ubuntu:**
```bash
# Activar entorno virtual
source .venv/bin/activate

# Opción 1: Script simplificado (recomendado)
python3 scripts/iniciar_api.py

# Opción 2: Uvicorn directo
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Opción 3: Con Gunicorn en desarrollo
gunicorn api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --reload
```

**Windows:**
```powershell
# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Opción 1: Script simplificado (recomendado)
python scripts/iniciar_api.py

# Opción 2: Uvicorn directo
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción en Servidor Ubuntu

**Opción 1: Gunicorn + Uvicorn (Recomendado)**
```bash
# Con 4 workers (ajustar según CPUs: (2 x núcleos) + 1)
gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/bots-api/access.log \
    --error-logfile /var/log/bots-api/error.log \
    --log-level info \
    --timeout 300 \
    --graceful-timeout 300
```

**Opción 2: Systemd Service**
```bash
# Ver sección "Servicio Systemd" para configuración completa
sudo systemctl start bots-api
sudo systemctl status bots-api
sudo journalctl -u bots-api -f  # Ver logs en tiempo real
```

**Opción 3: Uvicorn Standalone**
```bash
# Solo para testing, no recomendado para producción
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
# Build
docker build -t bots-api .

# Run
docker run -d -p 8000:8000 --env-file .env bots-api

# Con docker-compose
docker-compose up -d
```

### Ejecutar en Background (Sin Systemd)

**Linux/Ubuntu:**
```bash
# Con nohup
nohup gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    > /var/log/bots-api.log 2>&1 &

# Ver PID
echo $!

# Verificar proceso
ps aux | grep gunicorn

# Detener
pkill -f gunicorn
```

**Con screen o tmux:**
```bash
# Iniciar screen
screen -S bots-api

# Ejecutar API
python3 scripts/iniciar_api.py

# Detach: Ctrl+A, luego D

# Re-attach
screen -r bots-api

# Listar screens
screen -ls
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

# Listar todos los documentos (JSON estructurado)
Invoke-WebRequest "http://localhost:8000/api/v1/bot-simple/documents?limite=10" -UseBasicParsing

# Documentos recientes (JSON)
Invoke-WebRequest "http://localhost:8000/api/v1/bot-simple/recent-documents?limite=5" -UseBasicParsing

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

# Listar documentos
curl "http://localhost:8000/api/v1/bot-simple/documents?limite=10"

# Analizar documento específico por ID
curl -X POST "http://localhost:8000/api/v1/bot-simple/analyze-document" \
  -H "Content-Type: application/json" \
  -d '{"documento_id": 3, "pregunta": "Resume este documento"}'

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

# Listar todos los documentos disponibles
response = requests.get("http://localhost:8000/api/v1/bot-simple/documents?limite=20")
docs = response.json()
print(f"Total documentos: {docs['total']}")
for doc in docs['documentos']:
    print(f"  [{doc['id']}] {doc['title']} - {doc['created']}")

# Consulta al bot simple
response = requests.post(
    "http://localhost:8000/api/v1/bot-simple/query",
    json={"pregunta": "¿Qué dice el código de ética?"}
)
data = response.json()
print(data["respuesta"])
print(f"Tiempo: {data['tiempo_respuesta']}s")

# Analizar documento específico (usa ID de la lista anterior)
response = requests.post(
    "http://localhost:8000/api/v1/bot-simple/analyze-document",
    json={"documento_id": 3, "pregunta": "Resume este documento"}
)
print(response.json()["respuesta"])

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
// Listar documentos disponibles
const docsResponse = await fetch('http://localhost:8000/api/v1/bot-simple/documents?limite=10');
const docsData = await docsResponse.json();
console.log(`Total documentos: ${docsData.total}`);
docsData.documentos.forEach(doc => {
  console.log(`[${doc.id}] ${doc.title} - ${doc.created}`);
});

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

## 🌐 Despliegue en Producción

### Arquitectura de Despliegue

```
┌─────────────────────────────────────────────────┐
│     Cloudflare Zero Trust (Autenticación)       │
│              HTTPS/SSL Management               │
│           bots.tech-energy.lat                  │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│               Nginx (Reverse Proxy)             │
│         Logs, Rate Limiting, Compression        │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│          FastAPI (Gunicorn + Uvicorn)           │
│      Workers: 4  |  Port: 127.0.0.1:8000        │
└─────────────────────────────────────────────────┘
```

### 🔒 Cloudflare Zero Trust

La API está protegida con **Cloudflare Zero Trust** que gestiona:
- ✅ **Autenticación y autorización** (SSO, MFA, etc.)
- ✅ **SSL/TLS** (certificados automáticos)
- ✅ **DDoS protection** (capa 7)
- ✅ **WAF** (Web Application Firewall)
- ✅ **Rate limiting** por IP/usuario
- ✅ **Geo-blocking** y filtros personalizados

**Dominio de producción:** `https://bots.tech-energy.lat`

### 1. Configuración de Nginx

✅ **Configuración real en producción:**

Archivo: `/etc/nginx/sites-available/bots.conf`

```nginx
server {
    listen 80;
    server_name bots.tech-energy.lat;

    access_log /var/log/nginx/bots-api-access.log;
    error_log /var/log/nginx/bots-api-error.log;

    client_max_body_size 50M;

    real_ip_header CF-Connecting-IP;
    set_real_ip_from 0.0.0.0/0;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}
```

**Características:**
- Puerto `8001` para evitar conflicto con puerto 8000
- Timeouts de 300s para procesamiento IA
- WebSockets habilitados
- Headers de Cloudflare configurados

### 2. Activar Sitio

```bash
# Activar configuración
sudo ln -s /etc/nginx/sites-available/bots.conf /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/bots-api /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### 3. Servicio Systemd para Ubuntu 24.04

#### Preparación

```bash
# 1. Instalar Gunicorn si no está instalado
source /home/usuario/langchain/.venv/bin/activate
pip install gunicorn

# 2. Crear directorio para logs
sudo mkdir -p /var/log/bots-api
sudo chown $USER:$USER /var/log/bots-api

# 3. Verificar que el .env existe con las credenciales correctas
cat /home/usuario/langchain/.env
```

#### Crear Servicio

Crear `/etc/systemd/system/bots-api.service`:

```ini
[Unit]
Description=Bots API - FastAPI con Uvicorn y Gunicorn
After=network.target
Documentation=https://github.com/tu-usuario/langchain

[Service]
Type=notify
User=TU_USUARIO          # ⚠️ CAMBIAR por tu usuario (ej: ubuntu, admin, etc.)
Group=TU_USUARIO         # ⚠️ CAMBIAR por tu grupo
WorkingDirectory=/home/TU_USUARIO/langchain  # ⚠️ CAMBIAR ruta completa

# Variables de entorno
Environment="PATH=/home/TU_USUARIO/langchain/.venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=/home/TU_USUARIO/langchain"
EnvironmentFile=/home/TU_USUARIO/langchain/.env

# Comando de inicio
ExecStart=/home/TU_USUARIO/langchain/.venv/bin/gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/bots-api/access.log \
    --error-logfile /var/log/bots-api/error.log \
    --log-level info \
    --timeout 300 \
    --graceful-timeout 300 \
    --keep-alive 5

# Reinicio automático
Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=10

# Seguridad (opcional)
NoNewPrivileges=true
PrivateTmp=true

# Límites de recursos
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

#### Ejemplo con Rutas Reales

**Para usuario `ubuntu` en `/home/ubuntu/langchain`:**

```ini
[Unit]
Description=Bots API - FastAPI con Uvicorn
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/langchain

Environment="PATH=/home/ubuntu/langchain/.venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=/home/ubuntu/langchain"
EnvironmentFile=/home/ubuntu/langchain/.env

ExecStart=/home/ubuntu/langchain/.venv/bin/gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/bots-api/access.log \
    --error-logfile /var/log/bots-api/error.log \
    --timeout 300

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**✅ CONFIGURACIÓN REAL EN PRODUCCIÓN (bots.tech-energy.lat):**

Archivo: `/etc/systemd/system/bots.service`

```ini
[Unit]
Description=Gunicorn FastAPI para Bots Langchain
After=network.target

[Service]
User=tech-energy
Group=www-data
WorkingDirectory=/home/www/Bots_Langchain
Environment="PYTHONPATH=/home/www/Bots_Langchain"
Environment="PATH=/home/www/Bots_Langchain/.venv/bin"
ExecStart=/home/www/Bots_Langchain/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    api.main:app \
    --bind 127.0.0.1:8001 \
    --timeout 300

[Install]
WantedBy=multi-user.target
```

**Características clave:**
- Usuario: `tech-energy` con grupo `www-data`
- Puerto: `8001` (evita conflicto con otras apps en 8000)
- Timeout: `300s` para operaciones largas de IA
- Workers: `4` (ajustar según CPU disponibles)

### 4. Iniciar Servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Iniciar servicio
sudo systemctl start bots

# Verificar estado
sudo systemctl status bots

# Habilitar inicio automático
sudo systemctl enable bots

# Ver logs en tiempo real
sudo journalctl -u bots -f

# Reiniciar tras cambios en código
sudo systemctl restart bots
```

#### Comandos Útiles de Systemd

```bash
# Ver logs del servicio
sudo journalctl -u bots -n 50
sudo journalctl -u bots --since today
sudo journalctl -u bots --since "10 minutes ago"

# Probar configuración Nginx
sudo nginx -t && sudo systemctl reload nginx

# Ver si el puerto está activo
sudo lsof -i :8001

# Recargar configuración si editas el .service
sudo systemctl daemon-reload
sudo systemctl restart bots-api

# Verificar si está activo
systemctl is-active bots-api

# Ver procesos
ps aux | grep gunicorn
```

### 5. Configuración de Cloudflare Tunnel/Zero Trust

La API usa **Cloudflare Tunnel** para exponerse a Internet de forma segura sin abrir puertos en el firewall.

#### 5.1. Instalar cloudflared

```bash
# Descargar cloudflared para Ubuntu/Debian
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Verificar instalación
cloudflared --version

# Limpiar archivo de instalación
rm cloudflared.deb
```

#### 5.2. Autenticar con Cloudflare

```bash
# Autenticar (abre navegador para login)
cloudflared tunnel login

# Esto crea el archivo de credenciales en:
# ~/.cloudflared/cert.pem
```

#### 5.3. Crear el Tunnel

```bash
# Crear tunnel con nombre
cloudflared tunnel create bots-api

# Esto genera:
# 1. Un UUID único del tunnel
# 2. Archivo de credenciales: ~/.cloudflared/<UUID>.json
# 3. Registro en el dashboard de Cloudflare

# Ver tunnels existentes
cloudflared tunnel list

# Ejemplo de salida:
# ID                                   NAME      CREATED
# 12345678-1234-1234-1234-123456789abc bots-api  2026-03-13T10:00:00Z
```

#### 5.4. Configurar DNS

```bash
# Asociar dominio al tunnel
cloudflared tunnel route dns bots-api bots.tech-energy.lat

# Verificar en Cloudflare Dashboard:
# DNS > Records > Debería aparecer: bots.tech-energy.lat CNAME <UUID>.cfargotunnel.com
```

#### 5.5. Crear Archivo de Configuración

Crear `/home/www/Bots_Langchain/.cloudflared/config.yml`:

```bash
# Crear directorio si no existe
mkdir -p /home/www/Bots_Langchain/.cloudflared

# Crear archivo de configuración
sudo nano /home/www/Bots_Langchain/.cloudflared/config.yml
```

**Contenido de `config.yml`:**

```yaml
# Tunnel UUID (obtenerlo con: cloudflared tunnel list)
tunnel: 12345678-1234-1234-1234-123456789abc

# Archivo de credenciales del tunnel
credentials-file: /home/www/.cloudflared/12345678-1234-1234-1234-123456789abc.json

# Reglas de ingress
ingress:
  # Ruta 1: Todo el tráfico de bots.tech-energy.lat va a FastAPI local
  - hostname: bots.tech-energy.lat
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      tlsTimeout: 30s
      tcpKeepAlive: 30s
      keepAliveTimeout: 90s
      keepAliveConnections: 100
  
  # Ruta por defecto (obligatoria)
  - service: http_status:404

# Opciones de logging
loglevel: info
logfile: /var/log/cloudflared/cloudflared.log

# Métricas (opcional)
metrics: 0.0.0.0:2000
```

**Configuración Alternativa (con Nginx):**

Si usas Nginx como reverse proxy:

```yaml
tunnel: 12345678-1234-1234-1234-123456789abc
credentials-file: /home/www/.cloudflared/12345678-1234-1234-1234-123456789abc.json

ingress:
  - hostname: bots.tech-energy.lat
    service: http://localhost:80  # Apunta a Nginx en puerto 80
  
  - service: http_status:404
```

#### 5.6. Mover Credenciales (Opcional)

Por seguridad, puedes mover las credenciales al directorio del proyecto:

```bash
# Copiar credenciales
sudo cp ~/.cloudflared/*.json /home/www/Bots_Langchain/.cloudflared/

# Ajustar permisos
sudo chown -R www-data:www-data /home/www/Bots_Langchain/.cloudflared
sudo chmod 600 /home/www/Bots_Langchain/.cloudflared/*.json

# Actualizar ruta en config.yml
sudo nano /home/www/Bots_Langchain/.cloudflared/config.yml
# credentials-file: /home/www/Bots_Langchain/.cloudflared/<UUID>.json
```

#### 5.7. Crear Servicio Systemd para Cloudflared

Crear `/etc/systemd/system/cloudflared-tunnel.service`:

```ini
[Unit]
Description=Cloudflare Tunnel for Bots API
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/www/Bots_Langchain/.cloudflared/config.yml run
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared

# Directorio de trabajo
WorkingDirectory=/home/www/Bots_Langchain

# Variables de entorno (opcional)
Environment="TUNNEL_HOSTNAME=bots.tech-energy.lat"

[Install]
WantedBy=multi-user.target
```

#### 5.8. Iniciar Cloudflared

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/cloudflared
sudo chown www-data:www-data /var/log/cloudflared

# Recargar systemd
sudo systemctl daemon-reload

# Iniciar servicio
sudo systemctl start cloudflared-tunnel

# Verificar estado
sudo systemctl status cloudflared-tunnel

# Ver logs
sudo journalctl -u cloudflared-tunnel -f

# Habilitar inicio automático
sudo systemctl enable cloudflared-tunnel
```

#### 5.9. Verificar Funcionamiento

```bash
# 1. Verificar que cloudflared está corriendo
sudo systemctl status cloudflared-tunnel

# 2. Verificar conectividad del tunnel
cloudflared tunnel info bots-api

# 3. Test desde fuera del servidor
curl https://bots.tech-energy.lat/health

# 4. Ver métricas (si habilitaste metrics en config.yml)
curl http://localhost:2000/metrics

# 5. Ver logs
sudo journalctl -u cloudflared-tunnel -n 50
sudo tail -f /var/log/cloudflared/cloudflared.log
```

#### 5.10. Configurar Cloudflare Zero Trust (Autenticación)

**En el Dashboard de Cloudflare:**

1. **Ir a Zero Trust Dashboard:**
   - https://one.dash.cloudflare.com/
   - Selecciona tu account

2. **Crear Access Policy:**
   - Access > Applications > Add an application
   - Nombre: `Bots API`
   - Subdomain: `bots`
   - Domain: `tech-energy.lat`

3. **Configurar Políticas de Acceso:**
   ```
   Policy Name: Allow Team Members
   Action: Allow
   Include:
     - Emails: admin@tech-energy.lat, dev@tech-energy.lat
     - Email domain: tech-energy.lat
   ```

4. **Configurar Bypass para Endpoints Públicos:**
   ```
   Path: /health
   Action: Bypass
   
   Path: /docs
   Action: Allow (with authentication)
   
   Path: /api/*
   Action: Allow (with authentication)
   ```

5. **Configurar CORS (opcional):**
   - Settings > Network > CORS
   - Allowed origins: `https://tech-energy.lat`

#### 5.11. Troubleshooting Cloudflare

**Tunnel no conecta:**
```bash
# Verificar credenciales
cat ~/.cloudflared/cert.pem

# Probar tunnel manualmente
cloudflared tunnel --config /home/www/Bots_Langchain/.cloudflared/config.yml run

# Verificar DNS
dig bots.tech-energy.lat
nslookup bots.tech-energy.lat
```

**Error 502 Bad Gateway:**
```bash
# Verificar que FastAPI está corriendo
curl http://localhost:8000/health

# Verificar servicio bots-api
sudo systemctl status bots-api

# Ver logs de cloudflared
sudo journalctl -u cloudflared-tunnel -n 100
```

**Error de permisos:**
```bash
# Ajustar permisos del directorio
sudo chown -R www-data:www-data /home/www/Bots_Langchain/.cloudflared
sudo chmod 755 /home/www/Bots_Langchain/.cloudflared
sudo chmod 600 /home/www/Bots_Langchain/.cloudflared/*.json
sudo chmod 644 /home/www/Bots_Langchain/.cloudflared/config.yml
```

**Recrear tunnel desde cero:**
```bash
# Eliminar tunnel antiguo
cloudflared tunnel delete bots-api

# Crear nuevo
cloudflared tunnel create bots-api-new

# Actualizar DNS
cloudflared tunnel route dns bots-api-new bots.tech-energy.lat

# Actualizar config.yml con nuevo UUID
sudo nano /home/www/Bots_Langchain/.cloudflared/config.yml

# Reiniciar servicio
sudo systemctl restart cloudflared-tunnel
```

### 6. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

---

## 🔧 Solución de Problemas

### Puerto 8000 ocupado

**Windows PowerShell:**
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

**Linux/Ubuntu:**
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :8000
# O con netstat
sudo netstat -tulpn | grep :8000

# Ver detalles del proceso
ps aux | grep 8000

# Detener proceso específico
sudo kill -9 <PID>

# Detener todos los Gunicorn
pkill -f gunicorn

# Detener servicio systemd
sudo systemctl stop bots-api
```

### Errores al Instalar Dependencias en Ubuntu

**Error: "No module named '_sqlite3'"**
```bash
# Instalar sqlite3 development
sudo apt install -y libsqlite3-dev

# Recrear entorno virtual
deactivate  # Si está activado
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Error: "error: command 'gcc' failed"**
```bash
# Instalar herramientas de compilación
sudo apt install -y build-essential python3-dev

# Intentar de nuevo
pip install -r requirements.txt
```

**Error: "externally-managed-environment"**
```bash
# Asegúrate de estar en el entorno virtual
which python3
# Debe mostrar: /home/usuario/langchain/.venv/bin/python3

# Si no estás en venv:
source .venv/bin/activate

# Verificar
pip --version  # Debe mostrar la ruta del venv
```

**Error al instalar chromadb o hnswlib**
```bash
# Instalar dependencias de desarrollo
sudo apt install -y \
    python3.12-dev \
    libsqlite3-dev \
    pkg-config \
    build-essential

# Limpiar caché e instalar
pip cache purge
pip install --no-cache-dir chromadb hnswlib
```

**Error: "ModuleNotFoundError: No module named 'distutils'"**
```bash
# Python 3.12 deprecó distutils
sudo apt install -y python3-setuptools
pip install --upgrade setuptools
```

### Servidor no responde

**1. Verificar que está corriendo:**
```bash
# Probar endpoint de health
curl http://localhost:8000/health

# Con más detalles
curl -v http://localhost:8000/health
```

**2. Revisar logs:**

**Si usas systemd:**
```bash
# Ver logs en tiempo real
sudo journalctl -u bots-api -f

# Ver últimas 100 líneas
sudo journalctl -u bots-api -n 100

# Ver logs de hoy
sudo journalctl -u bots-api --since today
```

**Si ejecutas manualmente:**
```bash
# Los logs aparecen en la terminal donde ejecutaste el script
# O verifica:
cat /var/log/bots-api/access.log
cat /var/log/bots-api/error.log
```

**3. Error de Ollama (normal):**
```
⚠️ Error indexando documento: ... timeout 524
```
- Servidor remoto de Ollama sobrecargado
- API **continúa funcionando** de todos modos
- Solo afecta bot simple si Ollama es necesario

### Problemas con el Servicio Systemd

**El servicio no inicia:**
```bash
# Ver errores detallados
sudo systemctl status bots-api
sudo journalctl -u bots-api -n 50

# Verificar sintaxis del archivo .service
sudo systemd-analyze verify /etc/systemd/system/bots-api.service

# Verificar permisos del archivo .env
ls -la /home/usuario/langchain/.env
chmod 600 /home/usuario/langchain/.env
```

**Variables de entorno no se cargan:**
```bash
# Verificar que EnvironmentFile apunta al .env correcto
cat /etc/systemd/system/bots-api.service | grep EnvironmentFile

# Verificar contenido del .env
cat /home/usuario/langchain/.env

# Recargar configuración
sudo systemctl daemon-reload
sudo systemctl restart bots-api
```

**El servicio se detiene después de un tiempo:**
```bash
# Ver motivo del stop
sudo journalctl -u bots-api | grep -i "stopped\|failed"

# Aumentar timeout en el .service si es necesario
# Agregar en [Service]:
TimeoutStartSec=300
TimeoutStopSec=300
```

### ModuleNotFoundError en Producción

```bash
# Activar entorno virtual
source .venv/bin/activate

# Verificar que estás en el venv correcto
which python3
pip list | grep fastapi

# Reinstalar dependencias
pip install -r requirements.txt

# Si usas systemd, reiniciar servicio
sudo systemctl restart bots-api
```

### ChromaDB corrupto

```bash
# Detener servidor
sudo systemctl stop bots-api  # Si usas systemd
# O CTRL+C si ejecutas manualmente

# Backup y eliminar ChromaDB
mv chroma_db chroma_db.backup
# O eliminar completamente:
rm -rf chroma_db

# Reiniciar (recreará ChromaDB automáticamente)
sudo systemctl start bots-api  # O python3 scripts/iniciar_api.py
```

### Swagger UI no carga

1. **Limpiar caché del navegador:** CTRL + Shift + R
2. **Probar ReDoc:** http://localhost:8000/redoc o https://bots.tech-energy.lat/redoc
3. **Verificar servidor:** 
   ```bash
   curl http://localhost:8000/health
   ```
4. **Verificar logs de Nginx:**
   ```bash
   sudo tail -f /var/log/nginx/bots-api-error.log
   ```

### Problemas de Permisos

```bash
# Error: Permission denied al crear logs
sudo mkdir -p /var/log/bots-api
sudo chown $(whoami):$(whoami) /var/log/bots-api

# Error: Cannot write to chroma_db
cd /home/usuario/langchain
sudo chown -R $(whoami):$(whoami) chroma_db

# Verificar permisos del proyecto
ls -la
# Todos los archivos deben pertenecer a tu usuario
```

### Nginx no puede conectar a FastAPI

```bash
# Verificar que FastAPI está corriendo en 127.0.0.1:8000
curl http://127.0.0.1:8000/health

# Ver logs de Nginx
sudo tail -f /var/log/nginx/bots-api-error.log

# Verificar configuración de Nginx
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx

# Verificar que no hay firewall bloqueando
sudo ufw status
```

---

## 🛠️ Comandos Útiles

### Gestión del Servidor

**Iniciar API:**
```bash
# Desarrollo (Windows)
python scripts/iniciar_api.py

# Desarrollo (Linux/Ubuntu)
python3 scripts/iniciar_api.py

# Producción (systemd)
sudo systemctl start bots-api
sudo systemctl status bots-api
```

**Detener API:**
```bash
# Desarrollo: CTRL+C en la terminal

# Producción (systemd)
sudo systemctl stop bots-api

# Matar procesos
pkill -f gunicorn  # Linux
pkill -f uvicorn   # Linux
Get-Process python | Stop-Process -Force  # Windows
```

**Ver procesos:**
```bash
# Linux/Ubuntu
ps aux | grep python
ps aux | grep gunicorn
top -p $(pgrep -d',' python3)

# Windows
Get-Process python
Get-Process | Where-Object {$_.ProcessName -match "python"}
```

**Ver puerto 8000:**
```bash
# Linux/Ubuntu
sudo lsof -i :8000
sudo netstat -tulpn | grep :8000
ss -tulpn | grep :8000

# Windows
Get-NetTCPConnection -LocalPort 8000
netstat -ano | findstr :8000
```

### Gestión de Logs en Ubuntu

```bash
# Ver logs del servicio systemd
sudo journalctl -u bots-api -f              # Tiempo real
sudo journalctl -u bots-api -n 100          # Últimas 100 líneas
sudo journalctl -u bots-api --since today   # Hoy
sudo journalctl -u bots-api --since "10 minutes ago"
sudo journalctl -u bots-api --since "2024-03-13 10:00:00"

# Ver logs de archivos
tail -f /var/log/bots-api/access.log
tail -f /var/log/bots-api/error.log
less /var/log/bots-api/access.log

# Logs de Nginx
sudo tail -f /var/log/nginx/bots-api-access.log
sudo tail -f /var/log/nginx/bots-api-error.log
sudo tail -f /var/log/nginx/error.log

# Limpiar logs viejos
sudo truncate -s 0 /var/log/bots-api/access.log
sudo truncate -s 0 /var/log/bots-api/error.log

# Ver tamaño de logs
du -sh /var/log/bots-api/
du -sh /var/log/nginx/
```

### Gestión del Servicio Systemd

```bash
# Ver estado
sudo systemctl status bots-api
systemctl is-active bots-api
systemctl is-enabled bots-api

# Iniciar/Detener/Reiniciar
sudo systemctl start bots-api
sudo systemctl stop bots-api
sudo systemctl restart bots-api
sudo systemctl reload bots-api

# Habilitar/Deshabilitar inicio automático
sudo systemctl enable bots-api
sudo systemctl disable bots-api

# Editar configuración
sudo systemctl edit bots-api --full
sudo systemctl daemon-reload

# Ver configuración efectiva
systemctl cat bots-api
systemctl show bots-api
```

### Testing

```bash
# Test completo
python3 scripts/test_api_cliente.py

# Validar imports
python3 scripts/test_api_imports.py

# Health check
curl http://localhost:8000/health
curl https://bots.tech-energy.lat/health

# Health check con detalles
curl -v http://localhost:8000/health

# Test de endpoints
curl -X POST "http://localhost:8000/api/v1/bot-simple/query" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "test"}'

# Listar documentos
curl "http://localhost:8000/api/v1/bot-simple/documents?limite=5"
```

### Diagnóstico y Monitoreo

**Conectividad:**
```bash
# Test de puerto
nc -zv localhost 8000  # Linux
telnet localhost 8000  # Windows
nmap -p 8000 localhost

# Test desde otro servidor
curl -I https://bots.tech-energy.lat/health
```

**Recursos del sistema:**
```bash
# CPU y RAM de procesos Python
top -p $(pgrep -d',' python3)
htop -p $(pgrep -d',' python3)

# Memoria usada por el proceso
ps aux | grep gunicorn | awk '{sum+=$6} END {print sum/1024 " MB"}'

# Uso de disco
df -h
du -sh chroma_db/
du -sh .venv/

# Network stats
netstat -s
ss -s
```

**Performance:**
```bash
# Tiempo de respuesta
time curl http://localhost:8000/health

# Múltiples requests
for i in {1..10}; do curl -w "\nTime: %{time_total}s\n" http://localhost:8000/health; done

# Con Apache Bench
ab -n 100 -c 10 http://localhost:8000/health
```

### Mantenimiento

**Reindexar documentos:**
```bash
curl -X POST http://localhost:8000/api/v1/bot-avanzado/reindexar
curl -X POST https://bots.tech-energy.lat/api/v1/bot-avanzado/reindexar
```

**Ver estadísticas:**
```bash
curl http://localhost:8000/api/v1/bot-avanzado/stats | python3 -m json.tool
```

**Actualizar código en producción:**
```bash
# 1. Ir al directorio del proyecto
cd /home/usuario/langchain

# 2. Activar venv y hacer pull
source .venv/bin/activate
git pull origin main

# 3. Actualizar dependencias si es necesario
pip install -r requirements.txt

# 4. Reiniciar servicio
sudo systemctl restart bots-api

# 5. Verificar que funciona
sudo systemctl status bots-api
curl http://localhost:8000/health

# 6. Ver logs por si hay errores
sudo journalctl -u bots-api -n 50
```

**Backup:**
```bash
# Backup del .env
cp .env .env.backup

# Backup de ChromaDB
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup completo
tar -czf langchain_backup_$(date +%Y%m%d).tar.gz \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    /home/usuario/langchain/
```

### Nginx

```bash
# Verificar configuración
sudo nginx -t

# Recargar configuración
sudo systemctl reload nginx
sudo systemctl restart nginx

# Ver configuración activa
sudo nginx -T

# Estado del servicio
sudo systemctl status nginx

# Ver puertos en uso de Nginx
sudo netstat -tulpn | grep nginx
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

## � Guía Rápida de Despliegue en Producción

### Configuración Específica para bots.tech-energy.lat

Esta es la configuración completa para el servidor Ubuntu 24.04 con la ruta `/home/www/Bots_Langchain`.

#### 1. Preparar el Servidor Ubuntu

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y \
    python3.12 python3.12-venv python3.12-dev \
    python3-pip build-essential pkg-config \
    libsqlite3-dev git curl nginx

# Crear directorio del proyecto
sudo mkdir -p /home/www
cd /home/www

# Clonar repositorio (ajustar URL)
sudo git clone <tu-repo-url> Bots_Langchain
cd Bots_Langchain

# Ajustar permisos
sudo chown -R www-data:www-data /home/www/Bots_Langchain
```

#### 2. Configurar Entorno Virtual

```bash
# Crear entorno virtual
cd /home/www/Bots_Langchain
sudo -u www-data python3.12 -m venv .venv

# Activar venv
sudo -u www-data bash -c "source .venv/bin/activate && pip install --upgrade pip setuptools wheel"

# Instalar dependencias
sudo -u www-data bash -c "source .venv/bin/activate && pip install -r requirements.txt"
```

#### 3. Configurar Variables de Entorno

```bash
# Crear archivo .env
sudo nano /home/www/Bots_Langchain/.env
```

**Contenido del `.env`:**
```env
# Paperless-ngx
PAPERLESS_URL=https://paperless.tech-energy.lat
PAPERLESS_TOKEN=tu_token_aqui

# Ollama (Local)
OLLAMA_URL=https://ollama.tech-energy.lat
OLLAMA_MODEL=phi4-mini:latest

# OpenAI (Cloud)
LOCALIA=false
OPENAI_API_KEY=sk-...
OPENAI_MODEL_RAPIDO=gpt-4o-mini
OPENAI_MODEL_RAZONAMIENTO=gpt-4o

# ChromaDB
CHROMA_DB_PATH=./chroma_db
```

```bash
# Ajustar permisos del .env
sudo chown www-data:www-data /home/www/Bots_Langchain/.env
sudo chmod 600 /home/www/Bots_Langchain/.env
```

#### 4. Configurar Servicio Systemd

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/bots-api.service
```

**Copiar esta configuración exacta:**
```ini
[Unit]
Description=Bots API - FastAPI con Uvicorn (tech-energy.lat)
After=network.target
Documentation=https://bots.tech-energy.lat/docs

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/home/www/Bots_Langchain

Environment="PATH=/home/www/Bots_Langchain/.venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=/home/www/Bots_Langchain"
EnvironmentFile=/home/www/Bots_Langchain/.env

ExecStart=/home/www/Bots_Langchain/.venv/bin/gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/bots-api/access.log \
    --error-logfile /var/log/bots-api/error.log \
    --log-level info \
    --timeout 300 \
    --graceful-timeout 300

Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=10

NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/bots-api
sudo chown www-data:www-data /var/log/bots-api

# Recargar systemd e iniciar
sudo systemctl daemon-reload
sudo systemctl start bots-api
sudo systemctl enable bots-api

# Verificar estado
sudo systemctl status bots-api
```

> ⚠️ **Si el puerto 8000 está ocupado:** Edita el archivo systemd y cambia `--bind 127.0.0.1:8001` (también actualiza Nginx)

```bash
# Para usar puerto 8001, edita el systemd:
sudo nano /etc/systemd/system/bots.service

# Cambia la línea ExecStart:
ExecStart=/home/www/Bots_Langchain/.venv/bin/gunicorn api.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8001 \
    --timeout 300

# Luego recarga:
sudo systemctl daemon-reload
sudo systemctl restart bots
```

#### 5. Configurar Nginx

✅ **Configuración real en producción:**

```bash
sudo nano /etc/nginx/sites-available/bots.conf
```

**Contenido del archivo:**
```nginx
server {
    listen 80;
    server_name bots.tech-energy.lat;

    access_log /var/log/nginx/bots-api-access.log;
    error_log /var/log/nginx/bots-api-error.log;

    client_max_body_size 50M;

    real_ip_header CF-Connecting-IP;
    set_real_ip_from 0.0.0.0/0;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}
```

```bash
# Activar sitio
sudo ln -s /etc/nginx/sites-available/bots.conf /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

#### 6. Configurar Cloudflare Tunnel

```bash
# Instalar cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
rm cloudflared.deb

# Autenticar (abre navegador)
cloudflared tunnel login

# Crear tunnel
cloudflared tunnel create bots-api

# Obtener UUID del tunnel
cloudflared tunnel list
# Copiar el UUID que aparece (ej: 12345678-1234-1234-1234-123456789abc)

# Configurar DNS
cloudflared tunnel route dns bots-api bots.tech-energy.lat

# Crear directorio de configuración
sudo mkdir -p /home/www/Bots_Langchain/.cloudflared

# Copiar credenciales
sudo cp ~/.cloudflared/*.json /home/www/Bots_Langchain/.cloudflared/

# Crear archivo de configuración
sudo nano /home/www/Bots_Langchain/.cloudflared/config.yml
```

**Copiar esta configuración (reemplazar UUID):**
```yaml
tunnel: TU_UUID_AQUI
credentials-file: /home/www/Bots_Langchain/.cloudflared/TU_UUID_AQUI.json

ingress:
  - hostname: bots.tech-energy.lat
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
  
  - service: http_status:404

loglevel: info
logfile: /var/log/cloudflared/cloudflared.log
```

```bash
# Ajustar permisos
sudo chown -R www-data:www-data /home/www/Bots_Langchain/.cloudflared
sudo chmod 600 /home/www/Bots_Langchain/.cloudflared/*.json

# Crear directorio de logs
sudo mkdir -p /var/log/cloudflared
sudo chown www-data:www-data /var/log/cloudflared

# Crear servicio systemd
sudo nano /etc/systemd/system/cloudflared-tunnel.service
```

**Copiar esta configuración:**
```ini
[Unit]
Description=Cloudflare Tunnel for Bots API
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
ExecStart=/usr/local/bin/cloudflared tunnel --config /home/www/Bots_Langchain/.cloudflared/config.yml run
Restart=always
RestartSec=5
WorkingDirectory=/home/www/Bots_Langchain

[Install]
WantedBy=multi-user.target
```

```bash
# Activar servicio
sudo systemctl daemon-reload
sudo systemctl start cloudflared-tunnel
sudo systemctl enable cloudflared-tunnel

# Verificar estado
sudo systemctl status cloudflared-tunnel
```

#### 7. Verificar Instalación

```bash
# 1. Verificar que FastAPI está corriendo
sudo systemctl status bots
curl http://localhost:8001/health

# 2. Verificar Cloudflare Tunnel
sudo systemctl status cloudflared-tunnel
cloudflared tunnel info <tunnel-id>

# 3. Test desde internet
curl https://bots.tech-energy.lat/health

# 4. Ver documentación
# Abrir en navegador: https://bots.tech-energy.lat/docs

# 5. Ver logs
sudo journalctl -u bots -f
sudo journalctl -u cloudflared-tunnel -f
```

#### 8. Comandos para Actualizar

```bash
# Ir al directorio
cd /home/www/Bots_Langchain

# Pull de cambios
sudo -u tech-energy git pull origin main

# Actualizar dependencias si es necesario
sudo -u  tech-energy bash -c "source .venv/bin/activate && pip install -r requirements.txt"

# Reiniciar servicio
sudo systemctl restart bots

# Verificar que funciona
curl http://localhost:8001/health
sudo journalctl -u bots -n 50
```

#### Estructura de Directorios Final

```
/home/www/Bots_Langchain/
├── .env                          # Variables de entorno
├── .venv/                        # Entorno virtual Python
├── .cloudflared/                 # Configuración de Cloudflare
│   ├── config.yml
│   └── <UUID>.json
├── api/                          # Código de la API
├── bots/                         # Lógica de los bots
├── chroma_db/                    # Base de datos vectorial
├── requirements.txt              # Dependencias
└── scripts/                      # Scripts de utilidad

/etc/systemd/system/
├── bots-api.service              # Servicio FastAPI
└── cloudflared-tunnel.service    # Servicio Cloudflare

/var/log/
├── bots-api/                     # Logs de FastAPI
│   ├── access.log
│   └── error.log
├── cloudflared/                  # Logs de Cloudflare
│   └── cloudflared.log
└── nginx/                        # Logs de Nginx
    ├── bots-api-access.log
    └── bots-api-error.log
```

#### URLs de Producción

- **API**: https://bots.tech-energy.lat
- **Docs (Swagger)**: https://bots.tech-energy.lat/docs
- **ReDoc**: https://bots.tech-energy.lat/redoc
- **Health**: https://bots.tech-energy.lat/health

---

## �📄 Licencia

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
