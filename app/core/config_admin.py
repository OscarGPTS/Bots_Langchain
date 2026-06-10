"""Administración en caliente de parámetros OPERATIVOS del .env.

Permite que un panel (protegido con X-Admin-Token) lea y modifique un subconjunto
**no sensible** de la configuración. Los secretos (API keys, DSN, tokens) NO se
gestionan aquí: se cambian por bash en el servidor.

Estrategia:
  - Se valida contra una allowlist (`CAMPOS_EDITABLES`); cualquier otra clave se rechaza.
  - Se persiste en el archivo .env (preservando comentarios y el resto de líneas).
  - Se aplica "en caliente" mutando el objeto `settings` y limpiando cachés dependientes.
  - Los campos marcados `hot=False` requieren reiniciar el servicio para tomar efecto
    (se informa al usuario junto al comando exacto).
"""
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Raíz del proyecto (…/app/core/config_admin.py -> parents[2]).
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# Comando para reiniciar SOLO el servicio (no el servidor).
COMANDO_REINICIO = "sudo systemctl restart bots"

# Allowlist de parámetros operativos editables. NUNCA incluir secretos.
#   tipo: bool | int | str | enum     hot: True si aplica sin reiniciar
CAMPOS_EDITABLES: List[Dict[str, Any]] = [
    {"clave": "CONSULTAS_ENABLED", "etiqueta": "Módulo de consultas activo", "tipo": "bool", "hot": True,
     "descripcion": "Habilita/inhabilita el endpoint de consultas a datos."},
    {"clave": "VOICE_ENABLED", "etiqueta": "Voz activa", "tipo": "bool", "hot": True,
     "descripcion": "Habilita/inhabilita los endpoints de voz."},
    {"clave": "VOICE_BACKEND", "etiqueta": "Bot RAG para voz", "tipo": "enum", "hot": True,
     "opciones": ["simple", "avanzado"], "descripcion": "Qué bot responde las consultas de voz del RAG."},
    {"clave": "LLM_PROVIDER", "etiqueta": "Proveedor LLM de chat", "tipo": "enum", "hot": True,
     "opciones": ["auto", "ollama", "openai", "opencode"],
     "descripcion": "Aplica de inmediato al módulo de consultas; los bots RAG requieren reiniciar."},
    {"clave": "CONSULTAS_MAX_FILAS", "etiqueta": "Máx. filas por consulta", "tipo": "int", "hot": True,
     "min": 1, "max": 10000, "descripcion": "Tope global de filas devueltas."},
    {"clave": "CONSULTAS_SQL_TIMEOUT", "etiqueta": "Timeout SQL (s)", "tipo": "int", "hot": True,
     "min": 1, "max": 120, "descripcion": "Segundos máx. de ejecución por consulta SQL."},
    {"clave": "CONSULTAS_REST_TIMEOUT", "etiqueta": "Timeout REST (s)", "tipo": "int", "hot": True,
     "min": 1, "max": 120, "descripcion": "Timeout para orígenes REST."},
    {"clave": "CONSULTAS_LLM_PROVIDER", "etiqueta": "Proveedor LLM de consultas", "tipo": "enum", "hot": True,
     "opciones": ["auto", "ollama", "openai", "opencode"],
     "descripcion": "Proveedor SOLO para el generador NL→SQL; 'auto' hereda LLM_PROVIDER."},
    {"clave": "CONSULTAS_LLM_MODEL", "etiqueta": "Modelo LLM de consultas", "tipo": "str", "hot": True,
     "descripcion": "Modelo del proveedor elegido para NL→SQL (p.ej. deepseek-v4-flash); 'auto' = default del proveedor."},
    {"clave": "CONSULTAS_RAG_ENABLED", "etiqueta": "Contexto RAG de consultas", "tipo": "bool", "hot": True,
     "descripcion": "Inyectar al prompt NL→SQL los chunks de context/<origen>/ (si están indexados)."},
    {"clave": "CONSULTAS_RAG_TOP_K", "etiqueta": "Top-k contexto RAG", "tipo": "int", "hot": True,
     "min": 1, "max": 10, "descripcion": "Nº de chunks de contexto inyectados por consulta."},
    {"clave": "OLLAMA_MODEL", "etiqueta": "Modelo Ollama", "tipo": "str", "hot": False,
     "descripcion": "Modelo de Ollama para los bots RAG (requiere reinicio)."},
    {"clave": "OPENAI_MODEL_RAPIDO", "etiqueta": "Modelo OpenAI (rápido)", "tipo": "str", "hot": False,
     "descripcion": "Requiere reinicio."},
    {"clave": "OPENAI_MODEL_RAZONAMIENTO", "etiqueta": "Modelo OpenAI (razonamiento)", "tipo": "str", "hot": False,
     "descripcion": "Requiere reinicio."},
]

_POR_CLAVE = {c["clave"]: c for c in CAMPOS_EDITABLES}


def obtener_config() -> List[Dict[str, Any]]:
    """Devolver los campos editables con su metadato y valor actual (sin secretos)."""
    salida = []
    for campo in CAMPOS_EDITABLES:
        salida.append({**campo, "valor": getattr(settings, campo["clave"], None)})
    return salida


def _coaccionar(campo: Dict[str, Any], valor: Any) -> Any:
    """Convertir y validar un valor según el tipo declarado del campo."""
    tipo = campo["tipo"]
    if tipo == "bool":
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in ("1", "true", "yes", "on", "si", "sí")
    if tipo == "int":
        try:
            n = int(valor)
        except (TypeError, ValueError):
            raise ValueError(f"'{campo['clave']}' debe ser entero.")
        if "min" in campo and n < campo["min"]:
            raise ValueError(f"'{campo['clave']}' mínimo {campo['min']}.")
        if "max" in campo and n > campo["max"]:
            raise ValueError(f"'{campo['clave']}' máximo {campo['max']}.")
        return n
    # enum / str
    s = str(valor).strip()
    if tipo == "enum" and s not in campo.get("opciones", []):
        raise ValueError(f"'{campo['clave']}' debe ser uno de: {', '.join(campo['opciones'])}.")
    if not s:
        raise ValueError(f"'{campo['clave']}' no puede estar vacío.")
    return s


def _a_texto_env(valor: Any) -> str:
    """Representación del valor para escribir en el .env."""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


def _escribir_env(cambios: Dict[str, Any]) -> None:
    """Actualizar el .env preservando comentarios y el resto de líneas.

    Reemplaza la línea `CLAVE=...` (no comentada) conservando un comentario inline si
    existía; si la clave no estaba, la añade al final.
    """
    lineas = _ENV_PATH.read_text(encoding="utf-8").splitlines() if _ENV_PATH.exists() else []
    pendientes = dict(cambios)

    for i, linea in enumerate(lineas):
        despojada = linea.lstrip()
        if despojada.startswith("#") or "=" not in despojada:
            continue
        clave = despojada.split("=", 1)[0].strip()
        if clave in pendientes:
            comentario = ""
            if "#" in linea.split("=", 1)[1]:
                comentario = "  #" + linea.split("=", 1)[1].split("#", 1)[1]
            lineas[i] = f"{clave}={_a_texto_env(pendientes.pop(clave))}{comentario}"

    for clave, valor in pendientes.items():  # claves nuevas
        lineas.append(f"{clave}={_a_texto_env(valor)}")

    _ENV_PATH.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def _aplicar_hot(clave: str, valor: Any) -> None:
    """Aplicar el cambio en memoria (mutando settings) y limpiar cachés dependientes."""
    setattr(settings, clave, valor)
    if clave in ("LLM_PROVIDER", "CONSULTAS_LLM_PROVIDER", "CONSULTAS_LLM_MODEL"):
        from app.services.consultas.llm import obtener_llm
        obtener_llm.cache_clear()
    if clave == "CONSULTAS_SQL_TIMEOUT":
        from app.clients.mysql import reset_engines
        reset_engines()


def actualizar_config(cambios: Dict[str, Any]) -> Dict[str, Any]:
    """Validar, persistir y aplicar un conjunto de cambios operativos.

    Devuelve qué se aplicó en caliente, qué requiere reinicio y el comando exacto.
    Lanza ValueError si alguna clave no es editable o algún valor es inválido.
    """
    if not cambios:
        raise ValueError("No se enviaron cambios.")

    desconocidas = [k for k in cambios if k not in _POR_CLAVE]
    if desconocidas:
        raise ValueError(f"Parámetros no editables o inexistentes: {', '.join(desconocidas)}.")

    # Validar/coaccionar todo ANTES de escribir (todo-o-nada).
    normalizados = {k: _coaccionar(_POR_CLAVE[k], v) for k, v in cambios.items()}

    _escribir_env(normalizados)

    aplicados_hot: List[str] = []
    requieren_reinicio: List[str] = []
    for clave, valor in normalizados.items():
        campo = _POR_CLAVE[clave]
        if campo["hot"]:
            _aplicar_hot(clave, valor)
            aplicados_hot.append(clave)
        else:
            requieren_reinicio.append(clave)

    logger.info("[admin] config actualizada: hot=%s reinicio=%s", aplicados_hot, requieren_reinicio)

    mensaje = "Cambios guardados en .env."
    if aplicados_hot:
        mensaje += f" Aplicados en caliente: {', '.join(aplicados_hot)}."
    if requieren_reinicio:
        mensaje += (
            f" Requieren reiniciar el servicio: {', '.join(requieren_reinicio)} → "
            f"ejecuta `{COMANDO_REINICIO}`."
        )

    return {
        "aplicados_en_caliente": aplicados_hot,
        "requieren_reinicio": requieren_reinicio,
        "comando_reinicio": COMANDO_REINICIO if requieren_reinicio else None,
        "mensaje": mensaje,
    }
