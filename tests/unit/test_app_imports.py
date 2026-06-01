"""Smoke test: la aplicación y sus capas importan sin errores.

No requiere servicios externos: importar no instancia los bots (eso ocurre en
el lifespan / dependencias bajo demanda).
"""


def test_app_importable():
    from app.main import app
    assert app.title


def test_routers_registered():
    from app.main import app
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    # Routers v1 montados
    assert any(p.startswith("/api/v1/bot-simple") for p in paths)
    assert any(p.startswith("/api/v1/bot-avanzado") for p in paths)
    assert any(p.startswith("/api/v1/voz") for p in paths)


def test_settings_loads():
    from app.core.config import settings
    assert settings.OLLAMA_MODEL  # tiene un default


def test_schemas_importable():
    from app.schemas import QueryRequest, QueryResponse, HealthResponse
    assert QueryRequest and QueryResponse and HealthResponse


def test_legacy_api_shim():
    """El shim api.main:app sigue funcionando para gunicorn en producción."""
    from api.main import app as shim_app
    assert shim_app.title
