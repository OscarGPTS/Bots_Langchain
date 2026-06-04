"""Tests offline del formateador (tabla / gráfico, fase 2). No usa LLM ni red."""
from app.services.consultas.formateador import construir_respuesta

BASE = dict(
    origen_clave="rh_api",
    origen_tipo="rest_api",
    consulta="x",
    truncado=False,
    titulo="t",
    consulta_generada="GET /users",
    candidatos=["empleados"],
    advertencias=[],
    tiempo_respuesta=0.1,
)


def test_grafico_conteo_agrupa_por_categoria():
    r = construir_respuesta(
        **BASE,
        columnas=["nombre", "departamento"],
        filas=[["a", "IT"], ["b", "IT"], ["c", "Ventas"]],
        tipo_sugerido="grafico",
        formato_forzado=None,
        grafico_spec={"tipo_grafico": "bar", "columna_etiqueta": "departamento",
                      "columnas_valores": [], "agregacion": "conteo"},
    )
    assert r.tipo.value == "grafico"
    assert r.grafico.etiquetas == ["IT", "Ventas"]
    assert r.grafico.series[0]["data"] == [2, 1]
    assert r.tabla is not None  # se incluye la tabla cruda de respaldo


def test_grafico_suma_por_categoria():
    r = construir_respuesta(
        **BASE,
        columnas=["mes", "total"],
        filas=[["ene", "100"], ["ene", "50"], ["feb", "30"]],
        tipo_sugerido="grafico",
        formato_forzado=None,
        grafico_spec={"tipo_grafico": "line", "columna_etiqueta": "mes",
                      "columnas_valores": ["total"], "agregacion": "suma"},
    )
    assert r.grafico.etiquetas == ["ene", "feb"]
    assert r.grafico.series[0]["data"] == [150.0, 30.0]


def test_grafico_degrada_a_tabla_si_spec_invalida():
    r = construir_respuesta(
        **BASE,
        columnas=["nombre"],
        filas=[["a"], ["b"]],
        tipo_sugerido="grafico",
        formato_forzado=None,
        grafico_spec={"columna_etiqueta": "inexistente", "agregacion": "ninguna"},
    )
    assert r.tipo.value == "tabla"
    assert r.grafico is None
    assert any("gráfico" in a.lower() for a in r.meta.advertencias)


def test_formato_forzado_grafico_infiere_conteo():
    r = construir_respuesta(
        **BASE,
        columnas=["departamento", "nombre"],
        filas=[["IT", "a"], ["IT", "b"], ["RH", "c"]],
        tipo_sugerido="tabla",
        formato_forzado="grafico",
        grafico_spec=None,
    )
    assert r.tipo.value == "grafico"
    assert r.grafico.etiquetas == ["IT", "RH"]
    assert r.grafico.series[0]["data"] == [2, 1]


def test_tabla_normal():
    r = construir_respuesta(
        **BASE,
        columnas=["id", "nombre"],
        filas=[[1, "a"]],
        tipo_sugerido="tabla",
        formato_forzado=None,
        grafico_spec=None,
    )
    assert r.tipo.value == "tabla"
    assert r.tabla.total_filas == 1
    assert r.grafico is None
