"""Tests offline de la validación de SQL de solo lectura.

No tocan ninguna base de datos: solo validan el parseo/normalización.
"""
import pytest

from app.services.consultas.seguridad_sql import validar_y_asegurar

TABLAS = ["usuarios", "ordenes"]


def test_select_simple_inyecta_limit():
    sql, adv = validar_y_asegurar("SELECT id, nombre FROM usuarios", TABLAS, max_filas=500)
    assert "LIMIT 500" in sql.upper()
    assert any("LIMIT" in a.upper() for a in adv)


def test_select_recorta_limit_excesivo():
    sql, adv = validar_y_asegurar("SELECT id FROM usuarios LIMIT 10000", TABLAS, max_filas=500)
    assert "LIMIT 500" in sql.upper()
    assert any("recort" in a.lower() for a in adv)


def test_select_respeta_limit_valido():
    sql, _ = validar_y_asegurar("SELECT id FROM usuarios LIMIT 50", TABLAS, max_filas=500)
    assert "LIMIT 50" in sql.upper()


def test_with_cte_permitido():
    sql = "WITH u AS (SELECT id FROM usuarios) SELECT * FROM u"
    out, _ = validar_y_asegurar(sql, TABLAS, max_filas=100)
    assert out  # no lanza


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM usuarios",
        "UPDATE usuarios SET activo=0",
        "INSERT INTO usuarios (id) VALUES (1)",
        "DROP TABLE usuarios",
        "SELECT id FROM usuarios; DROP TABLE usuarios",  # multi-statement
        "SELECT * FROM usuarios INTO OUTFILE '/tmp/x'",
        "SELECT SLEEP(5)",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM otra_tabla",  # fuera de allowlist
    ],
)
def test_rechaza_no_lectura_o_no_permitido(sql):
    with pytest.raises(ValueError):
        validar_y_asegurar(sql, TABLAS, max_filas=500)
