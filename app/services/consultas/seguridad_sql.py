"""Validación de SQL de SOLO LECTURA (capa de software).

Defensa en capas junto al usuario MySQL read-only:
  1. Una sola sentencia y debe ser SELECT (o WITH/UNION de SELECT).
  2. Se rechaza DDL/DML, comandos crudos y `SELECT ... INTO`.
  3. Allowlist de tablas (solo las del catálogo del origen).
  4. Backstop por patrones peligrosos de MySQL (OUTFILE, LOAD_FILE, SLEEP, ...).
  5. LIMIT forzado/recortado al tope de filas.

`validar_y_asegurar` lanza `ValueError` si el SQL no es seguro; si es seguro
devuelve `(sql_normalizado, advertencias)`.
"""
import re
from typing import List, Sequence, Tuple

import sqlglot
from sqlglot import exp

# Patrones peligrosos (backstop por texto, además del análisis del AST).
_PATRONES_PROHIBIDOS = [
    r"\binto\s+outfile\b",
    r"\binto\s+dumpfile\b",
    r"\bload_file\s*\(",
    r"\bload\s+data\b",
    r"\bsleep\s*\(",
    r"\bbenchmark\s*\(",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\bcreate\b",
    r"\btruncate\b",
    r"\breplace\b",
    r"\bcall\b",
    r"\bhandler\b",
    r"\bset\s+",
]

# Esquemas de sistema que nunca deben consultarse.
_ESQUEMAS_PROHIBIDOS = {"information_schema", "mysql", "performance_schema", "sys"}


def _normalizar(nombre: str) -> str:
    return (nombre or "").strip().strip("`").lower()


def validar_y_asegurar(
    sql: str,
    tablas_permitidas: Sequence[str],
    max_filas: int,
) -> Tuple[str, List[str]]:
    """Valida que `sql` sea de solo lectura y seguro; devuelve (sql, advertencias).

    Lanza ValueError con un mensaje claro si no pasa alguna comprobación.
    """
    advertencias: List[str] = []
    sql = (sql or "").strip().rstrip(";").strip()
    if not sql:
        raise ValueError("El SQL generado está vacío.")

    # --- Backstop por texto (rápido y agnóstico al parser) ---
    sql_min = sql.lower()
    for patron in _PATRONES_PROHIBIDOS:
        if re.search(patron, sql_min):
            raise ValueError("El SQL contiene una operación no permitida (solo se permite SELECT).")

    # --- Análisis estructural con sqlglot ---
    try:
        sentencias = [s for s in sqlglot.parse(sql, read="mysql") if s is not None]
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"No se pudo analizar el SQL: {e}") from e

    if len(sentencias) != 1:
        raise ValueError("Solo se permite una sentencia SQL (sin multi-statement).")

    arbol = sentencias[0]

    # Debe ser un SELECT (o WITH/UNION/INTERSECT/EXCEPT de SELECT).
    if not isinstance(arbol, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise ValueError("Solo se permiten consultas SELECT.")

    # Sin comandos crudos ni SELECT ... INTO.
    if arbol.find(exp.Command):
        raise ValueError("El SQL contiene un comando no permitido.")
    if arbol.find(exp.Into):
        raise ValueError("No se permite 'SELECT ... INTO'.")

    # --- Allowlist de tablas ---
    permitidas = {_normalizar(t) for t in tablas_permitidas}
    # Nombres de CTE (WITH x AS ...): son alias internos, no tablas reales.
    ctes = {_normalizar(cte.alias_or_name) for cte in arbol.find_all(exp.CTE)}
    for tabla in arbol.find_all(exp.Table):
        esquema = _normalizar(tabla.db) if tabla.db else ""
        nombre = _normalizar(tabla.name)
        if esquema in _ESQUEMAS_PROHIBIDOS:
            raise ValueError("No se permite consultar esquemas del sistema.")
        if nombre in ctes:
            continue
        if nombre and nombre not in permitidas:
            raise ValueError(
                f"La tabla '{tabla.name}' no está permitida para este origen."
            )

    # --- LIMIT forzado / recortado ---
    arbol, adv_limit = _forzar_limit(arbol, max_filas)
    advertencias.extend(adv_limit)

    return arbol.sql(dialect="mysql"), advertencias


def _forzar_limit(arbol: exp.Expression, max_filas: int) -> Tuple[exp.Expression, List[str]]:
    """Inyecta LIMIT si falta o lo recorta si supera `max_filas`."""
    advertencias: List[str] = []
    limit_node = arbol.args.get("limit")

    if limit_node is None:
        return arbol.limit(max_filas), [f"Se aplicó LIMIT {max_filas} por defecto."]

    # Intentar leer el valor actual del LIMIT para recortarlo.
    try:
        actual = int(limit_node.expression.name)
    except (AttributeError, ValueError, TypeError):
        # No se pudo interpretar (p.ej. LIMIT con parámetro): forzar el tope.
        return arbol.limit(max_filas), [f"LIMIT no interpretable; se forzó {max_filas}."]

    if actual > max_filas:
        advertencias.append(f"LIMIT {actual} recortado a {max_filas}.")
        return arbol.limit(max_filas), advertencias

    return arbol, advertencias
