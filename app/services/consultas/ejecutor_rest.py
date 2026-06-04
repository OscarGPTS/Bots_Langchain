"""Cliente REST genérico de SOLO LECTURA (solo GET) para orígenes rest_api.

Seguridad:
  - Solo método GET.
  - La URL final debe pertenecer al `base_url` del origen (anti-SSRF).
  - Los `params` se filtran contra `params_permitidos` del recurso.
  - Timeout y tope de tamaño de respuesta.
"""
import os
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB de respuesta máx.


def _resolver_base_url(origen: Dict) -> str:
    env = origen.get("base_url_env")
    base = os.getenv(env) if env else origen.get("base_url")
    if not base:
        raise ValueError("El origen REST no tiene base_url configurada.")
    return base.rstrip("/")


def _mismo_host(base_url: str, url_final: str) -> bool:
    b, u = urlparse(base_url), urlparse(url_final)
    return (b.scheme, b.hostname, b.port) == (u.scheme, u.hostname, u.port)


def _url_segura(url: str) -> str:
    """URL sin credenciales (userinfo) para registrar en logs sin filtrar secretos."""
    p = urlparse(url)
    host = p.hostname or ""
    if p.port:
        host = f"{host}:{p.port}"
    return f"{p.scheme}://{host}{p.path}"


def ejecutar(origen: Dict, recurso: Dict, params: Dict[str, Any]) -> Tuple[List[str], List[List[Any]], List[Dict]]:
    """Llamar al endpoint GET del recurso y devolver (columnas, filas, registros).

    `registros` es la lista de dicts cruda (útil para resúmenes en texto).
    """
    base_url = _resolver_base_url(origen)
    endpoint = recurso.get("endpoint", "")
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    if not _mismo_host(base_url, url):
        raise ValueError("La URL del recurso no pertenece al base_url permitido.")

    # Filtrar params por allowlist del recurso.
    permitidos = set(recurso.get("params_permitidos", []) or [])
    params_filtrados = {k: v for k, v in (params or {}).items() if k in permitidos}

    timeout = int(origen.get("timeout", settings.CONSULTAS_REST_TIMEOUT))
    logger.info("[consultas] GET %s params=%s", _url_segura(url), params_filtrados)

    resp = requests.get(url, params=params_filtrados, timeout=timeout, stream=True)
    resp.raise_for_status()

    contenido = resp.raw.read(_MAX_BYTES + 1, decode_content=True)
    if len(contenido) > _MAX_BYTES:
        raise ValueError("La respuesta del origen REST es demasiado grande.")

    import json

    data = json.loads(contenido.decode("utf-8"))

    # Localizar la lista de registros (rules: 'lista_en', p.ej. "data").
    lista_en = recurso.get("lista_en")
    registros = data
    if isinstance(data, dict):
        registros = data.get(lista_en, data) if lista_en else data.get("data", data.get("results", data))
    if isinstance(registros, dict):
        registros = [registros]
    if not isinstance(registros, list):
        registros = []

    # Aplanar a columnas/filas (claves del primer nivel de cada registro).
    columnas: List[str] = []
    for reg in registros:
        if isinstance(reg, dict):
            for k in reg.keys():
                if k not in columnas:
                    columnas.append(k)

    max_filas = settings.CONSULTAS_MAX_FILAS
    filas = [
        [_aplanar(reg.get(col)) for col in columnas]
        for reg in registros[:max_filas]
        if isinstance(reg, dict)
    ]
    return columnas, filas, registros[:max_filas]


def _aplanar(valor: Any) -> Any:
    """Convertir objetos/listas anidados a una representación corta para la celda."""
    if isinstance(valor, dict):
        # Preferir un campo 'nombre'/'name' si existe; si no, str compacto.
        return valor.get("nombre") or valor.get("name") or str(valor)
    if isinstance(valor, list):
        return ", ".join(str(_aplanar(v)) for v in valor)
    return valor
