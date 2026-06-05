"""Tests offline del armado del DSN MySQL (dsn_env vs estilo Laravel)."""
import pytest

from app.clients.mysql import _resolver_dsn


def test_dsn_env_completo(monkeypatch):
    monkeypatch.setenv("MI_DSN", "mysql+pymysql://u:p@h:3306/db")
    assert _resolver_dsn("x", {"dsn_env": "MI_DSN"}) == "mysql+pymysql://u:p@h:3306/db"


def test_estilo_laravel_encodea_password(monkeypatch):
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_DATABASE", "cartera_clientes")
    monkeypatch.setenv("DB_USERNAME", "cartera_ro")
    monkeypatch.setenv("DB_PASSWORD", "C@rtera_ReadOnly_2026")  # '@' debe ir como %40
    dsn = _resolver_dsn("cartera_db", {"conexion_prefijo": "DB"})
    assert dsn == "mysql+pymysql://cartera_ro:C%40rtera_ReadOnly_2026@127.0.0.1:3306/cartera_clientes"


def test_estilo_laravel_password_vacia(monkeypatch):
    monkeypatch.setenv("DB_DATABASE", "db")
    monkeypatch.setenv("DB_USERNAME", "root")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "3306")
    dsn = _resolver_dsn("x", {"conexion_prefijo": "DB"})
    assert dsn == "mysql+pymysql://root@127.0.0.1:3306/db"  # sin ':' cuando no hay password


def test_faltan_datos_laravel(monkeypatch):
    monkeypatch.delenv("VENTAS_USERNAME", raising=False)
    monkeypatch.delenv("VENTAS_DATABASE", raising=False)
    with pytest.raises(ValueError):
        _resolver_dsn("ventas", {"conexion_prefijo": "VENTAS"})


def test_sin_configuracion():
    with pytest.raises(ValueError):
        _resolver_dsn("x", {})
