"""Utilidades de cliente para Paperless-ngx.

Centraliza la construcción de URLs de documentos (antes duplicada en las dos
rutas de la API).
"""
from typing import Dict, Optional

from app.core.config import settings


def build_document_urls(doc_id: int) -> Dict[str, Optional[str]]:
    """Construir URLs (download/preview/thumbnail) de un documento de Paperless.

    Las URLs incluyen el token como query param para acceso directo desde el
    frontend. ⚠️ Son privadas: no exponerlas públicamente ni registrarlas en logs.
    """
    paperless_url = (settings.PAPERLESS_URL or "").rstrip("/")
    if not paperless_url:
        return {"download_url": None, "preview_url": None, "thumbnail_url": None}

    token = settings.PAPERLESS_TOKEN or ""
    token_param = f"?token={token}" if token else ""

    return {
        "download_url": f"{paperless_url}/api/documents/{doc_id}/download/{token_param}",
        "preview_url": f"{paperless_url}/api/documents/{doc_id}/preview/{token_param}",
        "thumbnail_url": f"{paperless_url}/api/documents/{doc_id}/thumb/{token_param}",
    }
