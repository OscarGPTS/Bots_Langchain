# Guía de Despliegue en Producción - bots.tech-energy.lat

## Arquitectura del Sistema

```
Usuario → Cloudflare (HTTPS) → Cloudflared (Tunnel) → Nginx (80) → Gunicorn (8001) → FastAPI
```

## Configuración Real en Producción

### 1. Servicio Systemd

**Archivo:** `/etc/systemd/system/bots.service`

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

**Nota:** Se usa `api.main` porque el archivo está en `api/main.py`.

### 2. Configuración de Nginx

**Archivo:** `/etc/nginx/sites-available/bots.conf`

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

**Enlaces simbólicos:**
```bash
sudo ln -s /etc/nginx/sites-available/bots.conf /etc/nginx/sites-enabled/
```

### 3. Cloudflare Tunnel

**Configuración en Cloudflare One Dashboard:**
- Public Hostname: `bots.tech-energy.lat`
- Service: `HTTP://127.0.0.1:80`
- Estado: HEALTHY

### 4. Comandos de Mantenimiento

```bash
# Reiniciar API tras cambios en código
sudo systemctl restart bots

# Ver logs en tiempo real
sudo journalctl -u bots -f

# Probar configuración de Nginx
sudo nginx -t && sudo systemctl reload nginx

# Ver si puerto 8001 está activo
sudo lsof -i :8001

# Actualizar código
cd /home/www/Bots_Langchain
sudo -u tech-energy git pull origin main
sudo systemctl restart bots
```

### 5. Solución de Problemas Comunes

#### Error "ModuleNotFoundError: No module named 'main'"

**Causa:** Uso de `main:app` en lugar de `api.main:app`  
**Solución:** El módulo correcto es `api.main:app` porque el archivo está en `api/main.py`

#### Puerto 8001 ocupado

```bash
# Ver qué proceso usa el puerto
sudo lsof -i :8001

# Matar proceso si es necesario
fuser -k 8001/tcp
```

#### Error 502 Bad Gateway

```bash
# Verificar que FastAPI está corriendo
sudo systemctl status bots
curl http://localhost:8001/health

# Ver logs
sudo journalctl -u bots -n 100
```

#### Error 504 Gateway Timeout

- Aumentar `timeout` en gunicorn (actualmente 300s)
- Aumentar `proxy_read_timeout` en Nginx (actualmente 300s)

### 6. Verificación de Instalación

```bash
# 1. Servicio corriendo
sudo systemctl status bots

# 2. Puerto escuchando
sudo netstat -tulpn | grep 8001

# 3. Health check local
curl http://localhost:8001/health

# 4. Health check público
curl https://bots.tech-energy.lat/health

# 5. Documentación
# Abrir: https://bots.tech-energy.lat/docs
```

### 7. Estructura de Archivos

```
/home/www/Bots_Langchain/
├── .env                    # Variables de entorno
├── .venv/                  # Entorno virtual
├── api/
│   ├── main.py            # ← Punto de entrada FastAPI
│   ├── routes/
│   └── models/
├── bots/
├── chroma_db/
└── requirements.txt
```

## URLs de Producción

- **API:** https://bots.tech-energy.lat
- **Documentación:** https://bots.tech-energy.lat/docs
- **Health Check:** https://bots.tech-energy.lat/health
- **ReDoc:** https://bots.tech-energy.lat/redoc

## Especificaciones del Servidor

- **OS:** Ubuntu 24.04.3 LTS x86_64
- **Python:** 3.12.3
- **Ruta del proyecto:** `/home/www/Bots_Langchain`
- **Usuario:** `tech-energy` (grupo: `www-data`)
- **Puerto interno:** `8001`
- **Dominio:** `bots.tech-energy.lat`
