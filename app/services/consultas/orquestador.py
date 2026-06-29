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
    contexto_rag,
    conversacional,
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

    # Resolver por clave canónica O por alias (nombre del sistema, tag o URL).
    clave_canonica, origen = catalogo.resolver_origen(origen_clave)
    if origen is None:
        disponibles = ", ".join(catalogo.listar_origenes().keys()) or "(ninguno)"
        raise ConsultaError(
            f"No reconozco el origen '{origen_clave}'. Orígenes disponibles: {disponibles}."
        )
    origen_clave = clave_canonica  # usar siempre la canónica (caché de engine, logs, respuesta)

    tipo_origen = origen.get("tipo")

    # Capa conversacional: saludos / agradecimientos / ayuda → respuesta amigable,
    # sin generar SQL ni consultar la BD. Se omite si se fijó un `objetivo` concreto.
    if not objetivo:
        intencion = conversacional.detectar(consulta)
        if intencion:
            return conversacional.responder(intencion, origen, origen_clave, usuario, inicio)

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

    # Contexto semántico (vistas del sistema de origen); "" si no hay/no disponible.
    contexto_vistas = contexto_rag.recuperar_contexto(consulta, origen_clave)

    generado = generador.generar_sql(
        consulta,
        tablas_contexto,
        max_filas,
        join_hints,
        contexto_origen=origen.get("contexto"),
        contexto_vistas=contexto_vistas,
    )
    sql_seguro, advertencias = seguridad_sql.validar_y_asegurar(
        generado["sql"], tablas_permitidas=allowlist, max_filas=max_filas
    )

    columnas, filas, truncado = ejecutor_sql.ejecutar(origen_clave, origen, sql_seguro)

    # Fallback de gráfica: una serie basada en el historial mensual de ponderación
    # quedó vacía porque `proyecto_ponderacion_historial` no tiene snapshots. En vez
    # de responder "0 filas", se reintenta con la versión por banda usando la
    # ponderación ACTUAL (sin historial), preservando los filtros de la consulta.
    if (
        not filas
        and generado.get("tipo") == "grafico"
        and "proyecto_ponderacion_historial" in sql_seguro.lower()
    ):
        rescatado = _fallback_cartera_por_banda(
            consulta, tablas_contexto, max_filas, join_hints, origen,
            contexto_vistas, allowlist, origen_clave,
        )
        if rescatado is not None:
            columnas, filas, truncado, sql_seguro, generado_fb = rescatado
            # Conservar el título original; tomar tipo/gráfico de la consulta de rescate.
            generado = {**generado_fb, "titulo": generado.get("titulo", consulta[:120])}
            advertencias = (advertencias or []) + [
                "La evolución mensual no tiene datos (no hay snapshots en "
                "proyecto_ponderacion_historial); se muestra la cartera esperada por "
                "banda según la ponderación actual."
            ]

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


def _fallback_cartera_por_banda(
    consulta, tablas_contexto, max_filas, join_hints, origen,
    contexto_vistas, allowlist, origen_clave,
):
    """Reintenta una gráfica de cartera SIN `proyecto_ponderacion_historial`.

    Reescribe la consulta agrupando por banda con la ponderación ACTUAL
    (`proyectos.ponderacion`). Devuelve `(columnas, filas, truncado, sql, generado)`
    si la nueva consulta sí trae filas; `None` si no se pudo rescatar (sigue vacía o
    falla), para que el llamador conserve la respuesta original.
    """
    hint = (
        "[NOTA INTERNA] La tabla proyecto_ponderacion_historial está VACÍA (sin "
        "snapshots mensuales), por lo que una consulta basada en ella devuelve 0 "
        "filas. Reescribe la consulta SIN usar proyecto_ponderacion_historial ni "
        "ponderaciones: agrupa las oportunidades por banda usando la ponderación "
        "ACTUAL (proyectos.ponderacion) y devuelve por banda COUNT(*) AS ofertas, "
        "SUM(monto_usd) AS bruto, SUM(monto_usd*ponderacion/100) AS esperado, con "
        "tipo='grafico'. CONSERVA cualquier filtro por cliente/nombre de la consulta original."
    )
    try:
        generado = generador.generar_sql(
            f"{consulta}\n\n{hint}",
            tablas_contexto,
            max_filas,
            join_hints,
            contexto_origen=origen.get("contexto"),
            contexto_vistas=contexto_vistas,
        )
        sql_seguro, _adv = seguridad_sql.validar_y_asegurar(
            generado["sql"], tablas_permitidas=allowlist, max_filas=max_filas
        )
        if "proyecto_ponderacion_historial" in sql_seguro.lower():
            return None  # el modelo insistió en el historial; no rescatamos
        columnas, filas, truncado = ejecutor_sql.ejecutar(origen_clave, origen, sql_seguro)
        if not filas:
            return None
        return columnas, filas, truncado, sql_seguro, generado
    except Exception as e:  # noqa: BLE001
        logger.warning("Fallback de cartera por banda falló: %s", e)
        return None


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
            "alias": catalogo.alias_de(defn),
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
        "contexto_rag": contexto_rag.estado(),
    }
