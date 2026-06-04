"""Tests offline del catálogo: búsqueda por nombre y expansión de relaciones (FK)."""
from app.services.consultas import catalogo

ORIGEN = {
    "tipo": "sql_mysql",
    "tablas": [
        {
            "nombre": "proyectos",
            "keys": ["proyecto", "proyectos"],
            "relaciones": [
                {"tabla": "clientes", "on": "proyectos.cliente_id = clientes.id", "descripcion": "Cliente"},
            ],
            "columnas": [{"nombre": "id"}, {"nombre": "cliente_id"}, {"nombre": "monto_usd"}],
        },
        {
            "nombre": "clientes",
            "keys": ["cliente", "clientes"],
            "columnas": [{"nombre": "id"}, {"nombre": "razon_social"}],
        },
    ],
}


def test_item_por_nombre_case_insensitive():
    assert catalogo.item_por_nombre(ORIGEN, "Proyectos")["nombre"] == "proyectos"
    assert catalogo.item_por_nombre(ORIGEN, "no_existe") is None


def test_expandir_relaciones_agrega_tabla_fk_y_join():
    candidatos = [catalogo.item_por_nombre(ORIGEN, "proyectos")]
    tablas, joins = catalogo.expandir_relaciones(ORIGEN, candidatos)
    nombres = {t["nombre"] for t in tablas}
    assert nombres == {"proyectos", "clientes"}  # se añadió la relacionada
    assert any("clientes.id" in j for j in joins)  # hint de JOIN generado


def test_expandir_relaciones_sin_relaciones():
    candidatos = [catalogo.item_por_nombre(ORIGEN, "clientes")]
    tablas, joins = catalogo.expandir_relaciones(ORIGEN, candidatos)
    assert [t["nombre"] for t in tablas] == ["clientes"]
    assert joins == []
