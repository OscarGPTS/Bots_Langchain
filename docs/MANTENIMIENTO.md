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

### Opción rápida: script de despliegue

```bash
cd /home/www/Bots_Langchain
bash scripts/desplegar.sh            # pull → instala deps si cambió requirements → restart → health-check
bash scripts/desplegar.sh --reload   # igual pero sin downtime (requiere ExecReload, ver más abajo)
```
El script detecta si cambió `requirements.txt` (e instala solo en ese caso), omite el
reinicio si **solo** cambió documentación, verifica que el servicio quede `active` y
hace health-check de `/health` y `/api/v1/consultas/health`. No toca `.env` ni
`config/rules.yaml` (no versionados). Para hacerlo manual, sigue los casos de abajo.

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

## ⚙️ Panel de configuración (parámetros operativos)

Hay un panel web para ajustar **parámetros operativos no sensibles** sin entrar por SSH
(flags, modelo, límites, timeouts). **Los secretos** (API keys, DSN, tokens) **NO** se
gestionan aquí: se cambian por bash editando el `.env`.

- **URL:** `https://bots.tech-energy.lat/api/v1/admin/` (protegido por Cloudflare ZT).
- **Requisito:** definir `ADMIN_TOKEN` en el `.env`; el panel lo pide en el navegador y lo
  envía como header `X-Admin-Token`. Si `ADMIN_TOKEN` está vacío, el panel queda
  deshabilitado (403).

**Qué hace al guardar:**
- Escribe los cambios en el `.env` (preservando comentarios y el resto de variables).
- Aplica **en caliente** los parámetros marcados *"en caliente"* (no hace falta reiniciar):
  `CONSULTAS_ENABLED`, `VOICE_ENABLED`, `VOICE_BACKEND`, `LLM_PROVIDER` (módulo de
  consultas), `CONSULTAS_MAX_FILAS`, `CONSULTAS_SQL_TIMEOUT`, `CONSULTAS_REST_TIMEOUT`,
  `CONSULTAS_LLM_PROVIDER`, `CONSULTAS_LLM_MODEL` (LLM a medida del generador NL→SQL),
  `CONSULTAS_RAG_ENABLED` y `CONSULTAS_RAG_TOP_K` (contexto semántico).
- Para los marcados *"requiere reinicio"* (modelos de los bots RAG: `OLLAMA_MODEL`,
  `OPENAI_MODEL_*`), guarda el valor y muestra el comando exacto:
  ```bash
  sudo systemctl restart bots
  ```
  > Solo reinicia **el servicio**, no el servidor. `LLM_PROVIDER` aplica al instante al
  > módulo de consultas; para que los **bots RAG** lo tomen, también requiere ese reinicio.

**API equivalente** (por si se integra en otra UI):
```bash
# Leer parámetros editables
curl https://bots.tech-energy.lat/api/v1/admin/config -H "X-Admin-Token: <ADMIN_TOKEN>"
# Actualizar
curl -X PUT https://bots.tech-energy.lat/api/v1/admin/config \
  -H "X-Admin-Token: <ADMIN_TOKEN>" -H "Content-Type: application/json" \
  -d '{"cambios": {"CONSULTAS_MAX_FILAS": 1000, "LLM_PROVIDER": "opencode"}}'
```

> **Credenciales/secretos:** se cambian editando el `.env` por SSH (`nano .env` +
> `sudo systemctl restart bots`). Un flujo seguro con Auth0/Google para secretos queda
> como mejora futura.

### ⚠️ Importante: varios workers (Gunicorn `-w 4`)

El servicio corre con **4 workers** (procesos independientes). El "en caliente" aplica el
cambio **solo en el worker** que atendió la petición; el `.env` queda actualizado para
todos. Para que **todos los workers** tomen el valor sin cortar el servicio, haz un
**reload con recarga elegante** (sin downtime):

```bash
sudo systemctl reload bots     # requiere ExecReload (ver abajo); si no, usa restart
```

Habilitar `reload` (una sola vez) — añade esta línea en `[Service]` de
`/etc/systemd/system/bots.service` y `sudo systemctl daemon-reload`:
```ini
ExecReload=/bin/kill -s HUP $MAINPID
```
Gunicorn recarga sus workers con SIGHUP (releen el `.env`) sin tirar el servicio. Si no
configuras `ExecReload`, usa `sudo systemctl restart bots` (breve corte). Resumen:
- **Cambio "en caliente"** → efecto inmediato en 1 worker (suficiente para probar).
- **`reload`** → todos los workers, sin downtime (recomendado tras guardar).
- **`restart`** → todos los workers; obligatorio para los campos "requiere reinicio".

---

## 🧱 Notas por módulo

### Módulo de Consultas a Datos
- Requiere en `.env`: `CONSULTAS_ENABLED=true`, los DSN de cada origen (usuario MySQL de
  **solo lectura**) y un LLM capaz. El default del sistema ya es `opencode`/deepseek
  (solo falta `OPENCODE_API_KEY`); se puede fijar otro solo para consultas con
  `CONSULTAS_LLM_PROVIDER`/`CONSULTAS_LLM_MODEL`.
- El catálogo `config/rules.yaml` **no se versiona** (está en `.gitignore`): vive en el
  servidor. Si lo editas, `sudo systemctl restart bots`.
- **Contexto semántico (RAG)**: tras editar los `.md` de `context/<origen>/`, ejecutar
  `python scripts/indexar_contexto.py` (o `sincronizar_contexto.py`, que copia desde los
  repos fuente y reindexa). No requiere reiniciar el servicio.
- Tras cambios, valida: `curl -s http://127.0.0.1:8001/api/v1/consultas/health`
  (incluye el bloque `contexto_rag` con colección y nº de vectores). El proveedor de IA
  efectivo por módulo es visible en `GET /` (bloque `ia`).
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
