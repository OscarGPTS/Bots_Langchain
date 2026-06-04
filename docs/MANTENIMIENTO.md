# 🔧 Mantenimiento y operación (servidor de producción)

Runbook para operar el servicio ya desplegado: **aplicar cambios, instalar librerías,
reiniciar, ver logs y diagnosticar**. Pensado para que cualquiera del equipo pueda dar
mantenimiento aunque el responsable no esté.

> Para la instalación inicial completa (Nginx, Cloudflare Tunnel, systemd desde cero) ver
> [DEPLOYMENT.md](DEPLOYMENT.md). Para usar la API de consultas ver [API_CONSULTAS.md](API_CONSULTAS.md).

---

## 📌 Datos del entorno (producción)

| Dato | Valor |
|------|-------|
| Servidor / usuario | `tech-energy@tech-energy` |
| Ruta del proyecto | `/home/www/Bots_Langchain` |
| Entorno virtual | `/home/www/Bots_Langchain/.venv` |
| Servicio systemd | `bots` (`/etc/systemd/system/bots.service`) |
| Servidor app | Gunicorn + Uvicorn workers, `api.main:app`, `127.0.0.1:8001` |
| Acceso público | Cloudflare Zero Trust → `https://bots.tech-energy.lat` |
| Variables de entorno | `/home/www/Bots_Langchain/.env` |
| Catálogo de consultas | `/home/www/Bots_Langchain/config/rules.yaml` |

---

## ⚡ Aplicar cambios (lo más común)

Conéctate por SSH y sitúate en el proyecto:
```bash
cd /home/www/Bots_Langchain
```

### Caso A — Solo cambió código (sin nuevas librerías)
```bash
git pull                              # traer cambios
sudo systemctl restart bots           # reiniciar para que se vean
sudo systemctl status bots --no-pager # verificar que quedó "active (running)"
```

### Caso B — Cambió `requirements.txt` / hay librerías nuevas
```bash
git pull
source .venv/bin/activate             # entrar al venv
pip install -r requirements.txt       # instalar/actualizar dependencias
deactivate
sudo systemctl restart bots
```
> ⚠️ **Siempre** instala dentro del `.venv` (el servicio usa ese intérprete). Si instalas
> con el `pip` del sistema, el servicio no verá la librería.

### Caso C — Solo cambió `.env` o `config/rules.yaml`
```bash
nano .env                             # o nano config/rules.yaml
sudo systemctl restart bots           # el .env se lee al arrancar → hay que reiniciar
```

### Verificar que respondió
```bash
curl -s http://127.0.0.1:8001/health
curl -s http://127.0.0.1:8001/api/v1/consultas/health
# Público (a través de Cloudflare):
curl -s https://bots.tech-energy.lat/health
```

---

## 🔁 Comandos del servicio (systemd)

```bash
sudo systemctl restart bots      # reiniciar (tras cambios)
sudo systemctl stop bots         # detener
sudo systemctl start bots        # iniciar
sudo systemctl status bots       # estado actual
sudo systemctl reload-or-restart bots
sudo systemctl enable bots       # arrancar al boot (ya debería estar)
sudo systemctl is-active bots    # "active" / "failed"
```

> `restart` vs `reload`: esta app **no** soporta recarga en caliente; usa siempre
> `restart` para que los workers de Gunicorn tomen el código/`.env` nuevos.

---

## 📜 Logs

```bash
# En vivo (Ctrl+C para salir)
sudo journalctl -u bots -f

# Últimas N líneas / por tiempo
sudo journalctl -u bots -n 200 --no-pager
sudo journalctl -u bots --since "15 min ago" --no-pager
sudo journalctl -u bots --since today --no-pager

# Solo errores
sudo journalctl -u bots -p err --no-pager
```
Cada petición se registra con método, ruta, código y tiempo (`X-Process-Time`). El módulo
de consultas registra además el SQL/endpoint ejecutado (auditoría).

---

## 🧩 El servicio systemd

Archivo actual `/etc/systemd/system/bots.service`:
```ini
[Unit]
Description=Gunicorn FastAPI para Bots Langchain
After=network.target

[Service]
User=tech-energy
Group=www-data
WorkingDirectory=/home/www/Bots_Langchain
Environment="PYTHONPATH=/home/www/Bots_Langchain"
Environment="PATH=/home/www/Bots_Langchain/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/www/Bots_Langchain/.venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    api.main:app \
    --bind 127.0.0.1:8001 \
    --timeout 300

[Install]
WantedBy=multi-user.target
```

Si **editas** este archivo, recarga la definición antes de reiniciar:
```bash
sudo nano /etc/systemd/system/bots.service
sudo systemctl daemon-reload
sudo systemctl restart bots
```

Notas:
- `PATH` incluye los binarios del sistema → así `ffmpeg` (voz) es visible para el servicio.
- `api.main:app` es un *shim* que reexporta `app.main:app` (compatibilidad). Funciona igual.
- `--timeout 300` da margen a respuestas de IA largas. `-w 4` = 4 workers (ajustar a CPUs).

---

## ☁️ Cloudflare Zero Trust

El acceso público lo gestiona Cloudflare (autenticación, TLS, WAF) y el tráfico llega al
servicio local en `127.0.0.1:8001`. Para tareas de la app **no** hace falta tocar
Cloudflare. Solo es relevante si:
- Cambia el **dominio/hostname** o el **puerto** local → actualizar la config del túnel
  (`cloudflared`) y/o la aplicación en el panel Zero Trust.
- Falla el acceso externo pero `curl http://127.0.0.1:8001/health` **sí** responde →
  el problema está en Cloudflare/túnel, no en la app:
  ```bash
  sudo systemctl status cloudflared-tunnel   # o el nombre del servicio del túnel
  sudo journalctl -u cloudflared-tunnel -n 100 --no-pager
  ```
- Para dar acceso a alguien nuevo: agrégalo en la *Access Policy* de la aplicación en el
  panel de Cloudflare Zero Trust (no requiere cambios en el servidor).

---

## 🧱 Notas por módulo

### Módulo de Consultas a Datos
- Requiere en `.env`: `CONSULTAS_ENABLED=true`, los DSN de cada origen (usuario MySQL de
  **solo lectura**) y un `LLM_PROVIDER` capaz (p.ej. `opencode`/`openai`).
- El catálogo `config/rules.yaml` **no se versiona** (está en `.gitignore`): vive en el
  servidor. Si lo editas, `sudo systemctl restart bots`.
- Tras cambios, valida: `curl -s http://127.0.0.1:8001/api/v1/consultas/health`.
- Crear/renovar el usuario read-only: `scripts/crear_usuario_readonly_mysql.sql`.

### Voz (STT/TTS)
- Requiere `ffmpeg` en el sistema y los modelos descargados:
  ```bash
  sudo apt install -y ffmpeg
  source .venv/bin/activate && python scripts/descargar_modelos_voz.py
  ```
- Estado: `curl -s http://127.0.0.1:8001/api/v1/voz/health`.

### RAG / ChromaDB (documentos)
- Reindexar documentos (endpoint protegido con `X-Admin-Token`):
  ```bash
  curl -X POST http://127.0.0.1:8001/api/v1/bot-avanzado/reindexar -H "X-Admin-Token: <ADMIN_TOKEN>"
  ```

---

## 🚑 Diagnóstico rápido

**El servicio no arranca (`failed`):**
```bash
sudo systemctl status bots --no-pager
sudo journalctl -u bots -n 80 --no-pager     # leer el traceback real
```
Causas típicas: error de sintaxis tras un `git pull`, librería faltante (reinstala en el
venv), `.env`/`rules.yaml` mal formado, o el puerto ocupado.

**Puerto 8001 ocupado:**
```bash
sudo lsof -i :8001
sudo systemctl restart bots
```

**502 / no responde por el dominio pero sí en local:** ver sección Cloudflare arriba.

**Verificar el intérprete/venv del servicio:**
```bash
/home/www/Bots_Langchain/.venv/bin/python --version
/home/www/Bots_Langchain/.venv/bin/pip list | grep -Ei "fastapi|gunicorn|sqlglot|pymysql|pyyaml"
```

---

## ⏪ Rollback (volver a la versión anterior)

```bash
cd /home/www/Bots_Langchain
git log --oneline -n 5            # ver commits recientes
git checkout <hash_anterior>      # o: git reset --hard <hash_anterior>
# si requirements cambió: source .venv/bin/activate && pip install -r requirements.txt && deactivate
sudo systemctl restart bots
```
> Tras validar, vuelve a la rama con `git checkout master` (o la rama de despliegue).

---

## ✅ Checklist de despliegue de cambios

1. `cd /home/www/Bots_Langchain && git pull`
2. ¿Cambió `requirements.txt`? → `source .venv/bin/activate && pip install -r requirements.txt && deactivate`
3. ¿Cambió `.env` o `config/rules.yaml`? → editarlos en el servidor
4. `sudo systemctl restart bots`
5. `sudo systemctl status bots --no-pager` → debe estar `active (running)`
6. `curl -s http://127.0.0.1:8001/health` y el `/health` del módulo afectado
7. Revisar `sudo journalctl -u bots -n 50 --no-pager` por si hay warnings
