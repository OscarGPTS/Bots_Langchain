"""Factory de engines MySQL/MariaDB (cache por origen).

Cada origen SQL define su DSN mediante `dsn_env` en rules.yaml, que apunta a una
variable de entorno. El DSN DEBE usar un usuario de SOLO LECTURA (GRANT SELECT),
como capa de seguridad a nivel motor.
"""
import os
from typing import Dict, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engines: Dict[str, Engine] = {}


def _configurar_sesion(timeout_seg: int):
    """Listener que, al abrir cada conexión, fija sesión de solo lectura y timeout.

    Tolerante a MySQL vs MariaDB: cada motor usa una variable distinta para el
    timeout (`MAX_EXECUTION_TIME` en ms / `max_statement_time` en s). Las
    sentencias no soportadas se ignoran en silencio.
    """
    sentencias = [
        "SET SESSION TRANSACTION READ ONLY",          # ambos: bloquea escrituras
        f"SET SESSION MAX_EXECUTION_TIME={max(1, timeout_seg) * 1000}",  # MySQL (ms)
        f"SET SESSION max_statement_time={max(1, timeout_seg)}",          # MariaDB (s)
    ]

    def _on_connect(dbapi_conn, _conn_record):
        cur = dbapi_conn.cursor()
        for stmt in sentencias:
            try:
                cur.execute(stmt)
            except Exception:  # noqa: BLE001 - variable no soportada por este motor
                pass
        cur.close()

    return _on_connect


def obtener_engine(clave_origen: str, dsn_env: str) -> Engine:
    """Devolver (y cachear) el Engine de un origen SQL.

    Cada conexión se abre en modo de SOLO LECTURA y con timeout de ejecución en el
    servidor (defensa adicional, además de la validación de SQL).

    Lanza ValueError si la variable de entorno del DSN no está configurada.
    """
    if clave_origen in _engines:
        return _engines[clave_origen]

    dsn = os.getenv(dsn_env) or getattr(settings, dsn_env, None)
    if not dsn:
        raise ValueError(
            f"El origen '{clave_origen}' requiere la variable de entorno '{dsn_env}' (DSN MySQL read-only)."
        )

    engine = create_engine(
        dsn,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": settings.CONSULTAS_SQL_TIMEOUT},
    )
    event.listen(engine, "connect", _configurar_sesion(settings.CONSULTAS_SQL_TIMEOUT))
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
