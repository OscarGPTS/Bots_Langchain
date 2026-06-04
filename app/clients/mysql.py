"""Factory de engines MySQL/MariaDB (cache por origen).

Cada origen SQL define su DSN mediante `dsn_env` en rules.yaml, que apunta a una
variable de entorno. El DSN DEBE usar un usuario de SOLO LECTURA (GRANT SELECT),
como capa de seguridad a nivel motor.
"""
import os
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engines: Dict[str, Engine] = {}


def obtener_engine(clave_origen: str, dsn_env: str) -> Engine:
    """Devolver (y cachear) el Engine de un origen SQL.

    Aplica timeout de ejecución en el servidor (MAX_EXECUTION_TIME) y un modo de
    transacción de solo lectura como defensa adicional.

    Lanza ValueError si la variable de entorno del DSN no está configurada.
    """
    if clave_origen in _engines:
        return _engines[clave_origen]

    dsn = os.getenv(dsn_env) or getattr(settings, dsn_env, None)
    if not dsn:
        raise ValueError(
            f"El origen '{clave_origen}' requiere la variable de entorno '{dsn_env}' (DSN MySQL read-only)."
        )

    timeout_ms = max(1, settings.CONSULTAS_SQL_TIMEOUT) * 1000
    # init_command se ejecuta al abrir cada conexión del pool.
    init_command = (
        f"SET SESSION MAX_EXECUTION_TIME={timeout_ms}, "
        f"SESSION TRANSACTION READ ONLY"
    )

    engine = create_engine(
        dsn,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": settings.CONSULTAS_SQL_TIMEOUT,
            "init_command": init_command,
        },
    )
    _engines[clave_origen] = engine
    logger.info("Engine MySQL inicializado para origen '%s'", clave_origen)
    return engine


def reset_engines() -> None:
    """Cerrar y limpiar los engines cacheados (p.ej. al recargar configuración)."""
    for engine in _engines.values():
        try:
            engine.dispose()
        except Exception:  # noqa: BLE001
            pass
    _engines.clear()
