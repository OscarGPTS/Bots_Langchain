"""Shim de compatibilidad.

El código de la aplicación vive ahora en el paquete `app/`. Este módulo se
mantiene para que `gunicorn api.main:app` siga funcionando sin cambios en el
servidor. Migrar el servicio systemd a `app.main:app` cuando sea posible.
"""
from app.main import app

__all__ = ["app"]
