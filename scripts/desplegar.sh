#!/usr/bin/env bash
# =====================================================================
# Despliegue del día a día: pull → (instala deps si cambió requirements)
#                           → restart/reload del servicio → health-check
# =====================================================================
# Uso (en el servidor, como el usuario dueño del repo):
#   bash scripts/desplegar.sh              # pull + restart + verificación
#   bash scripts/desplegar.sh --reload     # usa 'systemctl reload' (sin downtime; requiere ExecReload)
#   bash scripts/desplegar.sh --force-deps # fuerza pip install aunque no cambie requirements.txt
#   bash scripts/desplegar.sh --no-restart # solo trae cambios, sin reiniciar
#
# Variables (override por entorno): SERVICE, PORT
#   SERVICE=bots PORT=8001 bash scripts/desplegar.sh
#
# NOTA: NO toca .env ni config/rules.yaml (están en .gitignore; viven en el servidor).
# =====================================================================
set -euo pipefail

SERVICE="${SERVICE:-bots}"
PORT="${PORT:-8001}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

ACCION_SERVICIO="restart"
FORCE_DEPS=0
DO_RESTART=1
for arg in "$@"; do
  case "$arg" in
    --reload) ACCION_SERVICIO="reload" ;;
    --force-deps) FORCE_DEPS=1 ;;
    --no-restart) DO_RESTART=0 ;;
    *) echo "Argumento desconocido: $arg"; exit 2 ;;
  esac
done

c_ok(){ echo -e "\033[32m✓\033[0m $*"; }
c_info(){ echo -e "\033[36m→\033[0m $*"; }
c_warn(){ echo -e "\033[33m!\033[0m $*"; }
c_err(){ echo -e "\033[31m✗\033[0m $*"; }

cd "$PROJECT_DIR"
echo "=================================================="
c_info "Proyecto:  $PROJECT_DIR"
c_info "Servicio:  $SERVICE (puerto $PORT)"
echo "=================================================="

# 1) Traer cambios -----------------------------------------------------
c_info "git pull..."
OLD_HEAD="$(git rev-parse HEAD)"
git pull --ff-only
NEW_HEAD="$(git rev-parse HEAD)"

if [ "$OLD_HEAD" = "$NEW_HEAD" ] && [ "$FORCE_DEPS" -eq 0 ]; then
  c_ok "Ya está al día (sin commits nuevos)."
  CHANGED=""
else
  CHANGED="$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" || true)"
  [ -n "$CHANGED" ] && c_ok "Cambios traídos:" && echo "$CHANGED" | sed 's/^/    /'
fi

# 2) Dependencias (solo si cambió requirements.txt o --force-deps) -----
if echo "$CHANGED" | grep -q "^requirements.txt$" || [ "$FORCE_DEPS" -eq 1 ]; then
  c_info "requirements.txt cambió → instalando dependencias en el venv..."
  "$VENV_PIP" install -r requirements.txt
  c_ok "Dependencias actualizadas."
else
  c_info "Sin cambios en requirements.txt (no se instala nada)."
fi

# 3) ¿Hace falta reiniciar? -------------------------------------------
# Si SOLO cambió documentación, se puede omitir el reinicio.
SOLO_DOCS=0
if [ -n "$CHANGED" ] && ! echo "$CHANGED" | grep -qvE '^(docs/|README\.md$|.*\.md$)'; then
  SOLO_DOCS=1
fi

if [ "$DO_RESTART" -eq 0 ]; then
  c_warn "Omitido el reinicio (--no-restart). Recuerda aplicar los cambios manualmente."
elif [ "$SOLO_DOCS" -eq 1 ]; then
  c_warn "Solo cambió documentación → no se reinicia el servicio."
else
  c_info "Aplicando con: sudo systemctl $ACCION_SERVICIO $SERVICE"
  sudo systemctl "$ACCION_SERVICIO" "$SERVICE"
  sleep 2
  if systemctl is-active --quiet "$SERVICE"; then
    c_ok "Servicio activo (running)."
  else
    c_err "El servicio NO quedó activo. Revisa: sudo journalctl -u $SERVICE -n 80 --no-pager"
    exit 1
  fi
fi

# 4) Health-check ------------------------------------------------------
check(){
  local ruta="$1"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}${ruta}" || echo 000)"
  if [ "$code" = "200" ]; then c_ok "GET $ruta → 200"; else c_warn "GET $ruta → $code"; fi
}
c_info "Verificando endpoints..."
check "/health"
check "/api/v1/consultas/health"

echo "=================================================="
c_ok "Despliegue terminado."
echo "Logs en vivo:  sudo journalctl -u $SERVICE -f"
