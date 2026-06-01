"""Dependencias de seguridad.

La autenticación de usuarios se delega a Cloudflare Zero Trust (perímetro).
Aquí solo se protegen operaciones administrativas sensibles (p.ej. /reindexar)
mediante un token de administración para defensa en profundidad.
"""
from fastapi import Header, HTTPException, status

from app.core.config import settings


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    """Exigir el header `X-Admin-Token` para endpoints administrativos.

    - Si `ADMIN_TOKEN` no está configurado, el endpoint queda deshabilitado (403).
    - Si el token no coincide, se rechaza (401).
    """
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación administrativa deshabilitada (ADMIN_TOKEN no configurado).",
        )
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de administración inválido.",
        )
