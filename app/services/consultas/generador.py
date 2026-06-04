"""Generación de la consulta a partir de lenguaje natural (vía LLM).

- SQL: produce un único SELECT en dialecto MySQL, acotado a las tablas candidatas.
- REST: elige un recurso del catálogo y arma los params permitidos.

El LLM solo recibe el esquema de los candidatos (no todo el catálogo) → menos tokens.
La salida se pide en JSON estricto y se parsea de forma defensiva.
"""
import json
import re
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.logging import get_logger
from app.services.consultas.llm import obtener_llm

logger = get_logger(__name__)


def _extraer_json(texto: str) -> Dict:
    """Extraer el primer objeto JSON de la respuesta del LLM (tolerante a ```json)."""
    if not texto:
        raise ValueError("Respuesta vacía del modelo.")
    # Quitar fences de código.
    limpio = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.MULTILINE).strip()
    # Tomar desde la primera { hasta la última }.
    inicio, fin = limpio.find("{"), limpio.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("El modelo no devolvió un JSON válido.")
    return json.loads(limpio[inicio : fin + 1])


def _esquema_tablas(candidatos: List[Dict]) -> str:
    """Texto compacto del esquema de las tablas candidatas (para el prompt SQL)."""
    bloques = []
    for t in candidatos:
        cols = []
        for c in t.get("columnas", []) or []:
            desc = f" -- {c['descripcion']}" if c.get("descripcion") else ""
            cols.append(f"  {c['nombre']} {c.get('tipo', '')}{desc}".rstrip())
        desc_t = f"  # {t['descripcion']}" if t.get("descripcion") else ""
        bloques.append(f"TABLA {t['nombre']}{desc_t}\n" + "\n".join(cols))
    return "\n\n".join(bloques)


def _esquema_recursos(candidatos: List[Dict]) -> str:
    """Texto compacto de los recursos REST candidatos (para el prompt intent)."""
    bloques = []
    for r in candidatos:
        params = ", ".join(r.get("params_permitidos", []) or []) or "(ninguno)"
        desc = f" — {r['descripcion']}" if r.get("descripcion") else ""
        bloques.append(f"RECURSO {r['nombre']}{desc}\n  params permitidos: {params}")
    return "\n\n".join(bloques)


def generar_sql(consulta: str, candidatos: List[Dict], max_filas: int, join_hints: Optional[List[str]] = None) -> Dict:
    """NL -> {sql, titulo, tipo}. El SELECT se valida después con seguridad_sql."""
    esquema = _esquema_tablas(candidatos)
    nombres = [t["nombre"] for t in candidatos]

    bloque_joins = ""
    if join_hints:
        bloque_joins = (
            "\n- Relaciones disponibles (usa JOIN cuando la pregunta lo requiera):\n  "
            + "\n  ".join(join_hints)
        )

    system = (
        "Eres un asistente que traduce preguntas en español a UNA consulta SQL de "
        "SOLO LECTURA para MySQL. Reglas estrictas:\n"
        "- Genera EXCLUSIVAMENTE una sentencia SELECT (o WITH ... SELECT).\n"
        "- PROHIBIDO: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, GRANT, ';' múltiple.\n"
        f"- Usa SOLO estas tablas y columnas: {', '.join(nombres)}.\n"
        f"- Incluye siempre un LIMIT (máximo {max_filas})."
        f"{bloque_joins}\n"
        "- tipo='tabla' si la pregunta pide un listado; 'texto' si pide un dato único o "
        "explicación; 'grafico' si pide graficar/visualizar/comparar magnitudes.\n"
        "- Si tipo='grafico', AGREGA en el propio SQL (GROUP BY, COUNT/SUM) y añade un "
        'objeto "grafico": {"tipo_grafico":"bar|line|pie","columna_etiqueta":"<col categoría>",'
        '"columnas_valores":["<col numérica>"],"agregacion":"ninguna"} usando los alias '
        "exactos del SELECT.\n"
        'Responde SOLO con JSON: {"sql":"...","titulo":"...","tipo":"tabla|texto|grafico","grafico":{...}|null}'
    )
    user = f"Esquema disponible:\n{esquema}\n\nPregunta del usuario:\n{consulta}"

    llm = obtener_llm()
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    data = _extraer_json(resp.content)

    if not data.get("sql"):
        raise ValueError("El modelo no generó una consulta SQL.")
    data.setdefault("tipo", "tabla")
    data.setdefault("titulo", consulta[:120])
    data.setdefault("grafico", None)
    return data


def generar_intent_rest(consulta: str, candidatos: List[Dict]) -> Dict:
    """NL -> {recurso, params, titulo, tipo} para un origen REST."""
    esquema = _esquema_recursos(candidatos)
    nombres = [r["nombre"] for r in candidatos]

    system = (
        "Eres un asistente que mapea una pregunta en español a una consulta de SOLO "
        "LECTURA sobre una API REST. Reglas:\n"
        f"- Elige UN recurso de esta lista: {', '.join(nombres)}.\n"
        "- Rellena 'params' SOLO con los params permitidos del recurso (puede ir vacío).\n"
        "- tipo='tabla' si se espera un listado; 'texto' si es un dato puntual; 'grafico' "
        "si pide graficar/visualizar/contar/comparar por categoría.\n"
        "- La API NO agrega datos: si tipo='grafico', añade un objeto \"grafico\": "
        '{"tipo_grafico":"bar|line|pie","columna_etiqueta":"<campo categoría>",'
        '"columnas_valores":["<campo numérico>"],"agregacion":"conteo|suma|ninguna"}. '
        "Usa 'conteo' para 'cuántos por X' (agrupa por columna_etiqueta y cuenta).\n"
        'Responde SOLO con JSON: {"recurso":"...","params":{...},"titulo":"...","tipo":"tabla|texto|grafico","grafico":{...}|null}'
    )
    user = f"Recursos disponibles:\n{esquema}\n\nPregunta del usuario:\n{consulta}"

    llm = obtener_llm()
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    data = _extraer_json(resp.content)

    if not data.get("recurso"):
        raise ValueError("El modelo no eligió un recurso REST.")
    data.setdefault("params", {})
    data.setdefault("tipo", "tabla")
    data.setdefault("titulo", consulta[:120])
    data.setdefault("grafico", None)
    return data


def resumir_resultados(consulta: str, columnas: List[str], filas: List[List], total: int) -> str:
    """Generar un resumen en lenguaje natural de los resultados (para tipo=texto)."""
    muestra = [dict(zip(columnas, fila)) for fila in filas[:20]]
    system = (
        "Resume en español, de forma breve y directa, los datos para responder la "
        "pregunta del usuario. No inventes datos fuera de los proporcionados."
    )
    user = (
        f"Pregunta: {consulta}\n"
        f"Total de filas: {total}\n"
        f"Datos (muestra): {json.dumps(muestra, ensure_ascii=False, default=str)}"
    )
    try:
        llm = obtener_llm()
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return resp.content.strip()
    except Exception as e:  # noqa: BLE001
        logger.warning("No se pudo generar resumen: %s", e)
        return f"Se encontraron {total} resultado(s)."
