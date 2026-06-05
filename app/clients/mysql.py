"""Factory de engines MySQL/MariaDB (cache por origen).

Un origen SQL define su conexión en rules.yaml de una de dos formas (siempre con un
usuario de SOLO LECTURA, como capa de seguridad a nivel motor):

  1) DSN completo:        dsn_env: CARTERA_DB_URL
                          CARTERA_DB_URL=mysql+pymysql://user:pass@host:3306/db
  2) Estilo Laravel:      conexion_prefijo: DB
                          DB_HOST=127.0.0.1 / DB_PORT=3306 / DB_DATABASE=...
                          DB_USERNAME=... / DB_PASSWORD=...   (DB_CONNECTION opcional)

La opción 2 evita tener que URL-encodear caracteres especiales de la contraseña
(p.ej. '@'): se codifica automáticamente al construir el DSN.
"""
import os
from typing import Dict, Optional
from urllib.parse import quote

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engines: Dict[str, Engine] = {}


def _resolver_dsn(clave_origen: str, origen: Dict) -> str:
    """Construir el DSN SQLAlchemy del origen desde `dsn_env` o `conexion_prefijo`."""
    # Opción 1: DSN completo en una sola variable de entorno.
    dsn_env = origen.get("dsn_env")
    if dsn_env:
        dsn = os.getenv(dsn_env) or getattr(settings, dsn_env, None)
        if not dsn:
            raise ValueError(
                f"El origen '{clave_origen}' requiere la variable de entorno '{dsn_env}' (DSN MySQL read-only)."
            )
        return dsn

    # Opción 2: componentes estilo Laravel con un prefijo (p.ej. DB -> DB_HOST, ...).
    prefijo = origen.get("conexion_prefijo")
    if prefijo:
        host = os.getenv(f"{prefijo}_HOST", "127.0.0.1")
        port = os.getenv(f"{prefijo}_PORT", "3306")
        database = os.getenv(f"{prefijo}_DATABASE")
        user = os.getenv(f"{prefijo}_USERNAME")
        password = os.getenv(f"{prefijo}_PASSWORD", "")
        if not (database and user):
            raise ValueError(
                f"El origen '{clave_origen}' necesita al menos {prefijo}_DATABASE y "
                f"{prefijo}_USERNAME en el .env."
            )
        # La contraseña se URL-encodea (maneja '@', ':', '/', etc.). Si va vacía, sin ':'.
        cred = f"{quote(user)}:{quote(password)}" if password else quote(user)
        return f"mysql+pymysql://{cred}@{host}:{port}/{database}"

    raise ValueError(
        f"El origen '{clave_origen}' debe definir 'dsn_env' o 'conexion_prefijo' en rules.yaml."
    )


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


def obtener_engine(clave_origen: str, origen: Dict) -> Engine:
    """Devolver (y cachear) el Engine de un origen SQL.

    Resuelve la conexión desde `dsn_env` o `conexion_prefijo` (estilo Laravel). Cada
    conexión se abre en modo de SOLO LECTURA y con timeout de ejecución en el servidor
    (defensa adicional, además de la validación de SQL).

    Lanza ValueError si la configuración de conexión está incompleta.
    """
    if clave_origen in _engines:
        return _engines[clave_origen]

    dsn = _resolver_dsn(clave_origen, origen)

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
