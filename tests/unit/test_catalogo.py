"""Tests offline del catálogo: búsqueda por nombre, relaciones (FK) y resolución por alias."""
import pytest

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


# --- Resolución de origen por clave canónica / alias / URL ---

ORIGENES_FAKE = {
    "origenes": {
        "cartera_db": {
            "tipo": "sql_mysql",
            "alias": ["cartera", "Cartera de Clientes", "https://cartera-clientes.tech-energy.lat/", "http://localhost:8001"],
        },
        "rh_api": {"tipo": "rest_api", "alias": ["rh", "recursos humanos"]},
    }
}


@pytest.fixture
def cargar_fake(monkeypatch):
    monkeypatch.setattr(catalogo, "_cache", ORIGENES_FAKE)
    monkeypatch.setattr(catalogo, "_cache_error", None)


@pytest.mark.parametrize("identificador,esperado", [
    ("cartera_db", "cartera_db"),            # clave canónica
    ("CARTERA_DB", "cartera_db"),            # case-insensitive
    ("cartera", "cartera_db"),               # alias simple
    ("Cartera de Clientes", "cartera_db"),   # alias con espacios/mayúsculas
    ("https://cartera-clientes.tech-energy.lat/", "cartera_db"),  # URL con esquema y / final
    ("cartera-clientes.tech-energy.lat", "cartera_db"),          # sin esquema
    ("http://localhost:8001/", "cartera_db"),                    # URL con / final
    ("rh", "rh_api"),
    ("recursos humanos", "rh_api"),
])
def test_resolver_origen(cargar_fake, identificador, esperado):
    clave, defn = catalogo.resolver_origen(identificador)
    assert clave == esperado and defn is not None


def test_resolver_origen_desconocido(cargar_fake):
    clave, defn = catalogo.resolver_origen("no_existe")
    assert clave is None and defn is None
