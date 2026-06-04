"""Ejecución de SELECT validados contra un origen MySQL read-only."""
from typing import Any, Dict, List, Tuple

from sqlalchemy import text

from app.clients.mysql import obtener_engine
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def ejecutar(clave_origen: str, origen: Dict, sql: str) -> Tuple[List[str], List[List[Any]], bool]:
    """Ejecutar el SELECT y devolver (columnas, filas, truncado).

    El SQL ya viene validado por `seguridad_sql`. Se materializan como máximo
    `max_filas` filas (tope del origen acotado por CONSULTAS_MAX_FILAS).
    """
    dsn_env = origen.get("dsn_env")
    if not dsn_env:
        raise ValueError(f"El origen '{clave_origen}' no define 'dsn_env'.")

    max_filas = min(
        int(origen.get("max_filas", settings.CONSULTAS_MAX_FILAS)),
        settings.CONSULTAS_MAX_FILAS,
    )

    engine = obtener_engine(clave_origen, dsn_env)

    # Auditoría: registrar el SQL ejecutado (sin credenciales).
    logger.info("[consultas] origen=%s SQL=%s", clave_origen, sql)

    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columnas = list(result.keys())
        filas_raw = result.fetchmany(max_filas + 1)  # +1 para detectar truncamiento

    truncado = len(filas_raw) > max_filas
    filas = [list(fila) for fila in filas_raw[:max_filas]]
    return columnas, filas, truncado
