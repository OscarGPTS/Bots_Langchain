"""Orquestador del módulo de consultas: une catálogo, generación, ejecución y formato.

Flujo:  consulta + origen → candidatos (keys) → LLM genera SQL/intent →
        validación + ejecución (solo lectura) → objeto estructurado.
"""
import time
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.consultas import ConsultaResponse
from app.services.consultas import (
    catalogo,
    ejecutor_rest,
    ejecutor_sql,
    formateador,
    generador,
    seguridad_sql,
)

logger = get_logger(__name__)


class ConsultaError(ValueError):
    """Error de negocio de una consulta (entrada inválida, origen inexistente, etc.)."""


def procesar_consulta(
    consulta: str,
    origen_clave: str,
    formato: Optional[str] = None,
    usuario: Optional[str] = None,
    objetivo: Optional[str] = None,
) -> ConsultaResponse:
    """Procesar una consulta de datos contra un origen del catálogo.

    `usuario` (nombre de quien consulta) se usa solo para personalizar la respuesta.
    `objetivo` apunta a una tabla/recurso concreto: si se indica, se ignora el matcher
    por palabras clave y se trabaja SOLO sobre esa entidad (más preciso).
    """
    if not settings.CONSULTAS_ENABLED:
        raise ConsultaError("El módulo de consultas está deshabilitado (CONSULTAS_ENABLED=false).")

    inicio = time.time()

    origen = catalogo.obtener_origen(origen_clave)
    if origen is None:
        disponibles = ", ".join(catalogo.listar_origenes().keys()) or "(ninguno)"
        raise ConsultaError(f"Origen '{origen_clave}' no existe. Disponibles: {disponibles}.")

    tipo_origen = origen.get("tipo")

    if objetivo:
        # Modo específico: usar solo la tabla/recurso indicado (sin matcher).
        item = catalogo.item_por_nombre(origen, objetivo)
        if item is None:
            disponibles = ", ".join(catalogo.nombres_items(origen)) or "(ninguno)"
            raise ConsultaError(
                f"El objetivo '{objetivo}' no existe en '{origen_clave}'. Disponibles: {disponibles}."
            )
        candidatos = [item]
    else:
        candidatos = catalogo.emparejar_candidatos(origen, consulta)
    if not candidatos:
        raise ConsultaError(f"El origen '{origen_clave}' no tiene tablas/recursos definidos.")

    nombres_candidatos = [c.get("nombre", "") for c in candidatos]

    if tipo_origen == "sql_mysql":
        return _procesar_sql(
            consulta, origen_clave, origen, candidatos, nombres_candidatos, formato, inicio, usuario
        )
    if tipo_origen == "rest_api":
        return _procesar_rest(
            consulta, origen_clave, origen, candidatos, nombres_candidatos, formato, inicio, usuario
        )

    raise ConsultaError(f"Tipo de origen no soportado: {tipo_origen!r}.")


def _procesar_sql(consulta, origen_clave, origen, candidatos, nombres, formato, inicio, usuario=None):
    """Flujo SQL: expande relaciones (FK) → genera SELECT → valida → ejecuta → formatea.

    `candidatos` son las tablas detectadas; se amplían con sus tablas relacionadas para
    permitir JOINs (allowlist). `nombres` se conserva como los candidatos originales para
    la trazabilidad (`meta.candidatos`).
    """
    max_filas = min(
        int(origen.get("max_filas", settings.CONSULTAS_MAX_FILAS)),
        settings.CONSULTAS_MAX_FILAS,
    )

    # Ampliar con tablas relacionadas (FK) y obtener los hints de JOIN.
    tablas_contexto, join_hints = catalogo.expandir_relaciones(origen, candidatos)
    allowlist = [t.get("nombre", "") for t in tablas_contexto]  # incluye relacionadas

    generado = generador.generar_sql(consulta, tablas_contexto, max_filas, join_hints)
    sql_seguro, advertencias = seguridad_sql.validar_y_asegurar(
        generado["sql"], tablas_permitidas=allowlist, max_filas=max_filas
    )

    columnas, filas, truncado = ejecutor_sql.ejecutar(origen_clave, origen, sql_seguro)

    return formateador.construir_respuesta(
        origen_clave=origen_clave,
        origen_tipo="sql_mysql",
        consulta=consulta,
        columnas=columnas,
        filas=filas,
        truncado=truncado,
        tipo_sugerido=generado.get("tipo", "tabla"),
        titulo=generado.get("titulo", consulta[:120]),
        formato_forzado=formato,
        consulta_generada=sql_seguro,
        candidatos=nombres,
        advertencias=advertencias,
        tiempo_respuesta=time.time() - inicio,
        grafico_spec=generado.get("grafico"),
        usuario=usuario,
    )


def _procesar_rest(consulta, origen_clave, origen, candidatos, nombres, formato, inicio, usuario=None):
    """Flujo REST: el LLM elige un recurso y sus params → GET (anti-SSRF) → formatea.

    La agregación para gráficos (si aplica) la resuelve el formateador, ya que las APIs
    REST no agregan en el servidor.
    """
    generado = generador.generar_intent_rest(consulta, candidatos)

    recurso = next((c for c in candidatos if c.get("nombre") == generado["recurso"]), None)
    if recurso is None:
        raise ConsultaError(f"El recurso '{generado['recurso']}' no está disponible en '{origen_clave}'.")

    columnas, filas, _registros = ejecutor_rest.ejecutar(origen, recurso, generado.get("params", {}))

    endpoint = recurso.get("endpoint", "")
    descripcion_consulta = f"GET {endpoint} params={generado.get('params', {})}"

    return formateador.construir_respuesta(
        origen_clave=origen_clave,
        origen_tipo="rest_api",
        consulta=consulta,
        columnas=columnas,
        filas=filas,
        truncado=len(filas) >= settings.CONSULTAS_MAX_FILAS,
        tipo_sugerido=generado.get("tipo", "tabla"),
        titulo=generado.get("titulo", consulta[:120]),
        formato_forzado=formato,
        consulta_generada=descripcion_consulta,
        candidatos=nombres,
        advertencias=[],
        tiempo_respuesta=time.time() - inicio,
        grafico_spec=generado.get("grafico"),
        usuario=usuario,
    )


def estado() -> dict:
    """Estado del módulo (para health)."""
    origenes = catalogo.listar_origenes()
    info = [
        {
            "clave": clave,
            "tipo": defn.get("tipo", "?"),
            "descripcion": defn.get("descripcion"),
            "tablas_o_recursos": catalogo.nombres_items(defn),
        }
        for clave, defn in origenes.items()
    ]
    return {
        "consultas_enabled": settings.CONSULTAS_ENABLED,
        "rules_cargado": catalogo.obtener_error() is None and bool(origenes),
        "rules_path": settings.RULES_PATH,
        "total_origenes": len(origenes),
        "origenes": info,
        "error_rules": catalogo.obtener_error(),
    }
