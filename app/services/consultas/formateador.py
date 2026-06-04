"""Construcción del objeto estructurado de respuesta (texto / tabla / gráfico).

Fase 2: a partir de las filas ejecutadas y una "spec de gráfico" (decidida por el
LLM o inferida), se arma `GraficoPayload` listo para Chart.js. La agregación
(`conteo`/`suma`) se hace aquí de forma determinista — útil sobre todo para
orígenes REST que no agregan en el servidor.
"""
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from app.schemas.consultas import (
    ConsultaMeta,
    ConsultaResponse,
    GraficoPayload,
    TablaPayload,
    TipoSalida,
)
from app.services.consultas import generador


def _es_numero(valor: Any) -> bool:
    if isinstance(valor, bool):
        return False
    if isinstance(valor, (int, float)):
        return True
    try:
        float(str(valor))
        return True
    except (TypeError, ValueError):
        return False


def _num(valor: Any) -> float:
    try:
        return float(str(valor))
    except (TypeError, ValueError):
        return 0.0


def _columnas_numericas(columnas: List[str], filas: List[List[Any]]) -> List[str]:
    """Columnas cuyos valores (en la muestra) son mayoritariamente numéricos."""
    numericas = []
    muestra = filas[:25] or []
    for i, col in enumerate(columnas):
        valores = [fila[i] for fila in muestra if i < len(fila) and fila[i] is not None]
        if valores and all(_es_numero(v) for v in valores):
            numericas.append(col)
    return numericas


def _inferir_spec(columnas: List[str], filas: List[List[Any]]) -> Optional[Dict]:
    """Inferir una spec de gráfico cuando no la dio el LLM (formato forzado)."""
    if not columnas:
        return None
    numericas = _columnas_numericas(columnas, filas)
    if numericas:
        etiqueta = next((c for c in columnas if c not in numericas), columnas[0])
        return {
            "tipo_grafico": "bar",
            "columna_etiqueta": etiqueta,
            "columnas_valores": numericas,
            "agregacion": "ninguna",
        }
    # Sin columnas numéricas: contar por la primera columna (categórica).
    return {
        "tipo_grafico": "bar",
        "columna_etiqueta": columnas[0],
        "columnas_valores": [],
        "agregacion": "conteo",
    }


def _construir_grafico(
    columnas: List[str], filas: List[List[Any]], spec: Dict
) -> Optional[GraficoPayload]:
    """Construir GraficoPayload aplicando la agregación indicada en `spec`."""
    if not spec:
        return None
    etiqueta = spec.get("columna_etiqueta")
    if etiqueta not in columnas:
        return None
    idx_lbl = columnas.index(etiqueta)
    agregacion = (spec.get("agregacion") or "ninguna").lower()
    tipo_grafico = spec.get("tipo_grafico") or "bar"
    valores_cols = [c for c in (spec.get("columnas_valores") or []) if c in columnas]

    if agregacion == "conteo":
        grupos: "OrderedDict[Any, int]" = OrderedDict()
        for fila in filas:
            clave = fila[idx_lbl]
            grupos[clave] = grupos.get(clave, 0) + 1
        return GraficoPayload(
            tipo_grafico=tipo_grafico,
            etiquetas=list(grupos.keys()),
            series=[{"label": "conteo", "data": list(grupos.values())}],
        )

    if agregacion == "suma" and valores_cols:
        grupos_suma: "OrderedDict[Any, Dict[str, float]]" = OrderedDict()
        for fila in filas:
            clave = fila[idx_lbl]
            acc = grupos_suma.setdefault(clave, {c: 0.0 for c in valores_cols})
            for c in valores_cols:
                acc[c] += _num(fila[columnas.index(c)])
        etiquetas = list(grupos_suma.keys())
        series = [
            {"label": c, "data": [grupos_suma[k][c] for k in etiquetas]}
            for c in valores_cols
        ]
        return GraficoPayload(tipo_grafico=tipo_grafico, etiquetas=etiquetas, series=series)

    # agregacion == "ninguna": usar las filas tal cual.
    if not valores_cols:
        valores_cols = _columnas_numericas(columnas, filas)
    if not valores_cols:
        return None
    etiquetas = [fila[idx_lbl] for fila in filas]
    series = [
        {"label": c, "data": [_num(fila[columnas.index(c)]) for fila in filas]}
        for c in valores_cols
    ]
    return GraficoPayload(tipo_grafico=tipo_grafico, etiquetas=etiquetas, series=series)


def _saludo(usuario: Optional[str]) -> str:
    """Frase de apertura personalizada (corta) para la respuesta."""
    u = (usuario or "").strip()
    return f"{u}, aquí tienes el resultado" if u else "Aquí tienes el resultado"


def _resolver_tipo(tipo_sugerido: str, formato_forzado: Optional[str], num_filas: int) -> TipoSalida:
    if formato_forzado:
        return TipoSalida(formato_forzado)
    if num_filas == 0:
        return TipoSalida.texto
    if tipo_sugerido in ("texto", "grafico"):
        return TipoSalida(tipo_sugerido)
    return TipoSalida.tabla


def construir_respuesta(
    *,
    origen_clave: str,
    origen_tipo: str,
    consulta: str,
    columnas: List[str],
    filas: List[List[Any]],
    truncado: bool,
    tipo_sugerido: str,
    titulo: str,
    formato_forzado: Optional[str],
    consulta_generada: str,
    candidatos: List[str],
    advertencias: List[str],
    tiempo_respuesta: float,
    grafico_spec: Optional[Dict] = None,
    usuario: Optional[str] = None,
) -> ConsultaResponse:
    """Ensamblar la `ConsultaResponse` a partir de los resultados ya ejecutados."""
    total = len(filas)
    tipo = _resolver_tipo(tipo_sugerido, formato_forzado, total)
    saludo = _saludo(usuario)

    tabla = None
    grafico = None
    texto = None

    # La tabla con los datos crudos se incluye siempre que haya filas (también
    # como respaldo del gráfico, para que el frontend pueda mostrar ambos).
    if total > 0:
        tabla = TablaPayload(
            columnas=columnas, filas=filas, total_filas=total, truncado=truncado
        )

    if tipo == TipoSalida.grafico:
        spec = grafico_spec or _inferir_spec(columnas, filas)
        grafico = _construir_grafico(columnas, filas, spec) if spec else None
        if grafico is None:
            # No se pudo graficar: degradar a tabla.
            tipo = TipoSalida.tabla
            advertencias = advertencias + ["No se pudo construir el gráfico; se devuelve la tabla."]
            texto = f"{saludo}: {total} registro(s)."
        else:
            texto = f"{saludo}: un gráfico con {len(grafico.etiquetas)} categoría(s)."
    elif tipo == TipoSalida.tabla:
        texto = f"{saludo}: {total} registro(s)." + (
            " El listado se recortó al máximo de filas." if truncado else ""
        )
    else:  # texto
        resumen = generador.resumir_resultados(consulta, columnas, filas, total)
        # Personalizar anteponiendo el nombre cuando se proporciona.
        u = (usuario or "").strip()
        texto = f"{u}, {resumen}" if u else resumen
        tabla = None  # en modo texto no devolvemos la tabla

    return ConsultaResponse(
        origen=origen_clave,
        tipo=tipo,
        titulo=titulo,
        texto=texto,
        tabla=tabla,
        grafico=grafico,
        meta=ConsultaMeta(
            origen_tipo=origen_tipo,
            consulta_generada=consulta_generada,
            candidatos=candidatos,
            advertencias=advertencias,
        ),
        tiempo_respuesta=round(tiempo_respuesta, 2),
    )
