"""Tests offline del panel de administración de parámetros operativos.

Usa un .env temporal (monkeypatch de _ENV_PATH) para no tocar el real.
"""
import pytest

from app.core import config_admin
from app.core.config import settings


@pytest.fixture
def env_tmp(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("CONSULTAS_MAX_FILAS=500  # tope\nOTRA=1\n", encoding="utf-8")
    monkeypatch.setattr(config_admin, "_ENV_PATH", p)
    return p


def test_obtener_config_incluye_editables_sin_secretos():
    claves = {c["clave"] for c in config_admin.obtener_config()}
    assert "CONSULTAS_MAX_FILAS" in claves and "LLM_PROVIDER" in claves
    # Nunca debe exponer secretos
    assert not ({"OPENAI_API_KEY", "OPENCODE_API_KEY", "CARTERA_DB_URL", "ADMIN_TOKEN"} & claves)


def test_rechaza_clave_no_editable(env_tmp):
    with pytest.raises(ValueError):
        config_admin.actualizar_config({"OPENAI_API_KEY": "sk-hack"})


def test_rechaza_entero_fuera_de_rango(env_tmp):
    with pytest.raises(ValueError):
        config_admin.actualizar_config({"CONSULTAS_SQL_TIMEOUT": 9999})


def test_rechaza_enum_invalido(env_tmp):
    with pytest.raises(ValueError):
        config_admin.actualizar_config({"LLM_PROVIDER": "gpt-magico"})


def test_actualiza_hot_y_persiste(env_tmp, monkeypatch):
    original = settings.CONSULTAS_MAX_FILAS
    try:
        res = config_admin.actualizar_config({"CONSULTAS_MAX_FILAS": 123})
        # se aplicó en caliente (mutó settings) y se persistió en el .env
        assert settings.CONSULTAS_MAX_FILAS == 123
        assert "CONSULTAS_MAX_FILAS=123" in env_tmp.read_text(encoding="utf-8")
        assert "CONSULTAS_MAX_FILAS" in res["aplicados_en_caliente"]
        assert "# tope" in env_tmp.read_text(encoding="utf-8")  # comentario preservado
    finally:
        settings.CONSULTAS_MAX_FILAS = original


def test_campo_no_hot_pide_reinicio(env_tmp):
    res = config_admin.actualizar_config({"OLLAMA_MODEL": "phi4-mini:latest"})
    assert "OLLAMA_MODEL" in res["requieren_reinicio"]
    assert res["comando_reinicio"] == config_admin.COMANDO_REINICIO
