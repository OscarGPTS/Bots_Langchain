"""Catálogo de reglas: carga `rules.yaml` y empareja la consulta con tablas/recursos.

El catálogo es la *allowlist* de lo que el bot puede consultar. El matcher reduce el
contexto enviado al LLM (menos tokens) buscando las `keys` de cada tabla/recurso en la
frase del usuario.
"""
import os
import re
import unicodedata
from typing import Dict, List, Optional

import yaml

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_cache: Optional[Dict] = None
_cache_error: Optional[str] = None


def _normalizar(texto: str) -> str:
    """Minúsculas + sin acentos, para comparar keys de forma robusta."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def cargar_reglas(forzar: bool = False) -> Dict:
    """Cargar (y cachear) el catálogo de reglas desde RULES_PATH.

    Devuelve {} si el archivo no existe o está mal formado (y deja el error en
    `obtener_error()`), para que el módulo degrade en vez de tumbar la API.
    """
    global _cache, _cache_error

    if _cache is not None and not forzar:
        return _cache

    ruta = settings.RULES_PATH
    if not os.path.exists(ruta):
        _cache, _cache_error = {}, f"No existe el archivo de reglas: {ruta}"
        logger.warning(_cache_error)
        return _cache

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict) or "origenes" not in data:
            raise ValueError("El catálogo debe tener una clave raíz 'origenes'.")
        _cache, _cache_error = data, None
        logger.info("Catálogo de reglas cargado: %d origen(es)", len(data.get("origenes", {})))
        return _cache
    except Exception as e:  # noqa: BLE001
        _cache, _cache_error = {}, f"Error al leer {ruta}: {e}"
        logger.error(_cache_error)
        return _cache


def obtener_error() -> Optional[str]:
    """Último error de carga del catálogo (o None)."""
    return _cache_error


def listar_origenes() -> Dict[str, Dict]:
    """Diccionario {clave: definicion} de todos los orígenes del catálogo."""
    return cargar_reglas().get("origenes", {}) or {}


def obtener_origen(clave: str) -> Optional[Dict]:
    """Definición de un origen por su clave, o None si no existe."""
    return listar_origenes().get(clave)


def _items_del_origen(origen: Dict) -> List[Dict]:
    """Lista unificada de tablas (SQL) o recursos (REST) del origen."""
    if origen.get("tipo") == "sql_mysql":
        return origen.get("tablas", []) or []
    if origen.get("tipo") == "rest_api":
        return origen.get("recursos", []) or []
    return []


def emparejar_candidatos(origen: Dict, consulta: str) -> List[Dict]:
    """Tablas/recursos cuyas `keys` aparecen en la consulta.

    Si ninguna coincide, devuelve TODOS los items del origen (para que el LLM
    elija con la lista compacta). Cada candidato se devuelve con su `_match_score`.
    """
    consulta_norm = _normalizar(consulta)
    # tokens como palabras completas para evitar que "user" matchee "usuario" parcial
    # de forma engañosa; usamos búsqueda por límite de palabra.
    candidatos: List[Dict] = []

    for item in _items_del_origen(origen):
        score = 0
        for key in item.get("keys", []) or []:
            key_norm = _normalizar(str(key))
            if re.search(rf"\b{re.escape(key_norm)}\b", consulta_norm):
                score += 1
        if score > 0:
            enriquecido = dict(item)
            enriquecido["_match_score"] = score
            candidatos.append(enriquecido)

    if candidatos:
        candidatos.sort(key=lambda x: x["_match_score"], reverse=True)
        return candidatos

    # Sin coincidencias: devolver todos (el LLM decide), sin score.
    return [dict(item) for item in _items_del_origen(origen)]


def nombres_items(origen: Dict) -> List[str]:
    """Nombres de las tablas/recursos de un origen (para health/listados)."""
    return [it.get("nombre", "") for it in _items_del_origen(origen)]


def item_por_nombre(origen: Dict, nombre: str) -> Optional[Dict]:
    """Tabla/recurso del origen por su nombre exacto (case-insensitive), o None."""
    objetivo = _normalizar(str(nombre))
    for it in _items_del_origen(origen):
        if _normalizar(str(it.get("nombre", ""))) == objetivo:
            return dict(it)
    return None


def expandir_relaciones(origen: Dict, candidatos: List[Dict]) -> tuple:
    """Para orígenes SQL: añade las tablas relacionadas (FK) y arma los hints de JOIN.

    Devuelve (tablas_contexto, join_hints):
      - tablas_contexto: candidatos + tablas referenciadas en `relaciones` (con su
        esquema), para que el LLM las conozca y el validador las permita.
      - join_hints: textos "a.col = b.col" para guiar los JOIN en el prompt.
    """
    tablas = list(candidatos)
    presentes = {_normalizar(str(t.get("nombre", ""))) for t in tablas}
    join_hints: List[str] = []

    for t in candidatos:
        for rel in t.get("relaciones", []) or []:
            rel_tabla = rel.get("tabla")
            cond = rel.get("on")
            if cond:
                desc = f" ({rel['descripcion']})" if rel.get("descripcion") else ""
                join_hints.append(f"{t.get('nombre')} ↔ {rel_tabla}: {cond}{desc}")
            if rel_tabla and _normalizar(str(rel_tabla)) not in presentes:
                rel_def = item_por_nombre(origen, rel_tabla)
                if rel_def:
                    tablas.append(rel_def)
                    presentes.add(_normalizar(str(rel_tabla)))

    return tablas, join_hints
