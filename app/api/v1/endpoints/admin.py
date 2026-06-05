"""Panel de administración de parámetros OPERATIVOS (no secretos).

- `GET  /api/v1/admin/config`  → parámetros editables + valores (requiere X-Admin-Token).
- `PUT  /api/v1/admin/config`  → guarda en .env y aplica en caliente lo posible.
- `GET  /api/v1/admin`         → dashboard web mínimo (HTML); pide el token en el navegador.

Los secretos (API keys, DSN, tokens) NO se gestionan aquí; se cambian por bash.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from app.core import config_admin
from app.core.security import require_admin_token
from app.schemas.admin import ActualizarConfigRequest, ActualizarConfigResponse, ConfigResponse

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get(
    "/config",
    response_model=ConfigResponse,
    dependencies=[Depends(require_admin_token)],
    summary="Leer parámetros operativos editables",
)
async def leer_config():
    """Devolver los parámetros operativos editables con su valor actual (sin secretos)."""
    return ConfigResponse(campos=config_admin.obtener_config())


@router.put(
    "/config",
    response_model=ActualizarConfigResponse,
    dependencies=[Depends(require_admin_token)],
    summary="Actualizar parámetros operativos (.env, en caliente)",
)
async def actualizar_config(request: ActualizarConfigRequest):
    """Validar, persistir en `.env` y aplicar en caliente lo posible.

    Lo que no se puede aplicar en caliente se informa junto al comando de reinicio.
    """
    try:
        return ActualizarConfigResponse(**config_admin.actualizar_config(request.cambios))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Dashboard web mínimo. El token se introduce en el navegador y viaja por header."""
    return HTMLResponse(_DASHBOARD_HTML)


_DASHBOARD_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Panel de configuración</title>
<style>
  :root{--b:#2563eb;--bg:#0f172a;--card:#1e293b;--mut:#94a3b8;--ok:#16a34a;--warn:#d97706}
  *{box-sizing:border-box} body{margin:0;font:15px system-ui,Segoe UI,Roboto,sans-serif;background:#0b1220;color:#e2e8f0}
  .wrap{max-width:720px;margin:0 auto;padding:24px}
  h1{font-size:20px} .mut{color:var(--mut)}
  .card{background:var(--card);border:1px solid #334155;border-radius:12px;padding:16px;margin:12px 0}
  label{display:block;font-weight:600;margin-bottom:4px}
  .desc{font-size:12px;color:var(--mut);margin-bottom:8px}
  input,select{width:100%;padding:8px;border-radius:8px;border:1px solid #475569;background:#0b1220;color:#e2e8f0}
  input[type=checkbox]{width:auto}
  .tag{font-size:11px;padding:2px 8px;border-radius:999px;margin-left:8px}
  .hot{background:#064e3b;color:#86efac} .restart{background:#7c2d12;color:#fdba74}
  button{background:var(--b);color:#fff;border:0;border-radius:8px;padding:10px 16px;font-weight:600;cursor:pointer}
  button:disabled{opacity:.5;cursor:default}
  .row{display:flex;gap:10px;align-items:center;margin-bottom:14px}
  #msg{white-space:pre-wrap;margin-top:12px}
  .tok{display:flex;gap:8px}
</style></head><body><div class="wrap">
  <h1>⚙️ Panel de configuración <span class="mut">(parámetros operativos)</span></h1>
  <p class="mut">Solo parámetros no sensibles. Los secretos (API keys, DSN) se cambian por bash.</p>
  <div class="card">
    <label>Token de administración (X-Admin-Token)</label>
    <div class="tok"><input id="token" type="password" placeholder="ADMIN_TOKEN"><button onclick="cargar()">Cargar</button></div>
  </div>
  <form id="form"></form>
  <div class="row"><button id="save" onclick="guardar()" disabled>Guardar cambios</button></div>
  <div id="msg" class="mut"></div>
</div>
<script>
const $=s=>document.querySelector(s); let CAMPOS=[];
function headers(){return {"Content-Type":"application/json","X-Admin-Token":$("#token").value};}
async function cargar(){
  $("#msg").textContent="Cargando...";
  try{
    const r=await fetch("/api/v1/admin/config",{headers:headers()});
    if(!r.ok){throw new Error((await r.json()).detail||r.status);}
    CAMPOS=(await r.json()).campos; render(); $("#save").disabled=false; $("#msg").textContent="";
  }catch(e){$("#msg").textContent="❌ "+e.message;}
}
function render(){
  $("#form").innerHTML=CAMPOS.map(c=>{
    const tag=c.hot?'<span class="tag hot">en caliente</span>':'<span class="tag restart">requiere reinicio</span>';
    let input;
    if(c.tipo==="bool") input=`<input type="checkbox" id="f_${c.clave}" ${c.valor?"checked":""}>`;
    else if(c.tipo==="enum") input=`<select id="f_${c.clave}">${c.opciones.map(o=>`<option ${String(c.valor)===o?"selected":""}>${o}</option>`).join("")}</select>`;
    else if(c.tipo==="int") input=`<input type="number" id="f_${c.clave}" value="${c.valor??""}" min="${c.min??""}" max="${c.max??""}">`;
    else input=`<input type="text" id="f_${c.clave}" value="${c.valor??""}">`;
    return `<div class="card"><label>${c.etiqueta} ${tag}</label><div class="desc">${c.clave} — ${c.descripcion||""}</div>${input}</div>`;
  }).join("");
}
function valor(c){const el=$("#f_"+c.clave); return c.tipo==="bool"?el.checked:(c.tipo==="int"?Number(el.value):el.value);}
async function guardar(){
  const cambios={}; CAMPOS.forEach(c=>cambios[c.clave]=valor(c));
  $("#msg").textContent="Guardando...";
  try{
    const r=await fetch("/api/v1/admin/config",{method:"PUT",headers:headers(),body:JSON.stringify({cambios})});
    const d=await r.json(); if(!r.ok) throw new Error(d.detail||r.status);
    $("#msg").innerHTML="✅ "+d.mensaje+(d.comando_reinicio?`\\n\\n💡 Reinicia el servicio:\\n  ${d.comando_reinicio}`:"");
  }catch(e){$("#msg").textContent="❌ "+e.message;}
}
</script></body></html>"""
