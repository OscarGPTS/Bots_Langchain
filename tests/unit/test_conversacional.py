"""Tests offline de la detección conversacional (sin LLM ni BD)."""
import pytest

from app.services.consultas import conversacional

ORIGEN = {
    "tipo": "sql_mysql",
    "tablas": [{"nombre": "clientes"}, {"nombre": "proyectos"}],
}


@pytest.mark.parametrize("texto,esperado", [
    ("hola", "saludo"),
    ("Buenos días", "saludo"),
    ("hola, ¿qué tal?", "saludo"),
    ("gracias!", "agradecimiento"),
    ("muchas gracias", "agradecimiento"),
    ("adiós", "despedida"),
    ("hasta luego", "despedida"),
    ("¿qué puedes hacer?", "ayuda"),
    ("ayuda", "ayuda"),
    ("no sé qué preguntar", "ayuda"),
    ("¿qué información tienes?", "ayuda"),
])
def test_detecta_conversacional(texto, esperado):
    assert conversacional.detectar(texto) == esperado


@pytest.mark.parametrize("texto", [
    "cuántos clientes hay por sector",
    "top 5 proyectos por monto en usd",
    "dame la lista de clientes activos",
    "monto total por cliente",
])
def test_consultas_reales_no_son_conversacionales(texto):
    assert conversacional.detectar(texto) is None


def test_respuesta_ayuda_lista_entidades_y_personaliza():
    r = conversacional.responder("ayuda", ORIGEN, "cartera_db", "Óscar", inicio=0.0)
    assert r.tipo.value == "texto"
    assert "Óscar" in r.texto
    assert "clientes" in r.texto and "proyectos" in r.texto  # lista capacidades
    assert r.tabla is None and r.grafico is None
    assert r.meta.consulta_generada is None


def test_respuesta_saludo_sin_usuario():
    r = conversacional.responder("saludo", ORIGEN, "cartera_db", None, inicio=0.0)
    assert r.tipo.value == "texto"
    assert r.texto.startswith("¡Hola!")
