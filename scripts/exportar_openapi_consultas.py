"""Exporta la especificación del módulo de Consultas para compartir con el equipo.

Genera dos archivos en docs/:
  - openapi_consultas.json : OpenAPI 3.x recortado a las rutas /api/v1/consultas
                             (importable en Swagger UI, Insomnia, etc.).
  - postman_consultas.json : Colección Postman v2.1 con los 3 endpoints y ejemplos.

Uso:
    python scripts/exportar_openapi_consultas.py
"""
import json
import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path al ejecutar como script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

PREFIJO = "/api/v1/consultas"
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
BASE_URL = "http://localhost:8000"


def _refs_en(obj, acc):
    """Recolectar recursivamente los nombres de schema referenciados (#/components/schemas/X)."""
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            acc.add(ref.split("/")[-1])
        for v in obj.values():
            _refs_en(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _refs_en(v, acc)


def _cerrar_schemas(nombres, todos):
    """Expandir el conjunto de schemas para incluir los referenciados transitivamente."""
    pendientes = set(nombres)
    resueltos = set()
    while pendientes:
        n = pendientes.pop()
        if n in resueltos or n not in todos:
            continue
        resueltos.add(n)
        sub = set()
        _refs_en(todos[n], sub)
        pendientes |= sub - resueltos
    return resueltos


def exportar_openapi() -> dict:
    """OpenAPI recortado a las rutas del módulo de consultas + sus schemas."""
    full = app.openapi()
    paths = {p: item for p, item in full["paths"].items() if p.startswith(PREFIJO)}

    usados = set()
    _refs_en(paths, usados)
    todos = full.get("components", {}).get("schemas", {})
    usados = _cerrar_schemas(usados, todos)

    spec = {
        "openapi": full["openapi"],
        "info": {
            "title": "API de Consultas a Datos",
            "description": "NL → SQL / API REST (solo lectura) con salida estructurada (texto/tabla/gráfico). Ver docs/API_CONSULTAS.md.",
            "version": full["info"]["version"],
        },
        "servers": [{"url": BASE_URL}, {"url": "https://bots.tech-energy.lat"}],
        "paths": paths,
        "components": {"schemas": {k: todos[k] for k in sorted(usados)}},
        "tags": [{"name": "Consultas"}],
    }
    return spec


def construir_postman() -> dict:
    """Colección Postman v2.1 con los 3 endpoints y ejemplos listos para usar."""
    return {
        "info": {
            "name": "API Consultas a Datos",
            "description": "Consultas NL → SQL / API REST (solo lectura). Ver docs/API_CONSULTAS.md.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseUrl", "value": BASE_URL}],
        "item": [
            {
                "name": "Consultar (texto)",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "url": {"raw": "{{baseUrl}}/api/v1/consultas/", "host": ["{{baseUrl}}"], "path": ["api", "v1", "consultas", ""]},
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps(
                            {
                                "consulta": "cuántos clientes hay por sector",
                                "origen": "cartera_db",
                                "formato": None,
                                "objetivo": None,
                                "usuario": "Óscar",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    },
                    "description": "consulta + origen → objeto estructurado (texto/tabla/grafico).",
                },
            },
            {
                "name": "Consultar por voz (audio)",
                "request": {
                    "method": "POST",
                    "header": [],
                    "url": {"raw": "{{baseUrl}}/api/v1/consultas/voz", "host": ["{{baseUrl}}"], "path": ["api", "v1", "consultas", "voz"]},
                    "body": {
                        "mode": "formdata",
                        "formdata": [
                            {"key": "file", "type": "file", "src": [], "description": "Audio webm/wav/mp3/ogg/m4a"},
                            {"key": "origen", "value": "cartera_db", "type": "text"},
                            {"key": "usuario", "value": "Óscar", "type": "text"},
                            {"key": "objetivo", "value": "", "type": "text", "description": "(opcional) tabla/recurso específico"},
                            {"key": "formato", "value": "", "type": "text", "description": "(opcional) texto|tabla|grafico"},
                            {"key": "responder_voz", "value": "true", "type": "text"},
                        ],
                    },
                    "description": "audio → transcripción → consulta → objeto + resumen hablado (audio_base64).",
                },
            },
            {
                "name": "Health",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {"raw": "{{baseUrl}}/api/v1/consultas/health", "host": ["{{baseUrl}}"], "path": ["api", "v1", "consultas", "health"]},
                    "description": "Estado del módulo y orígenes disponibles.",
                },
            },
        ],
    }


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)

    openapi_path = os.path.join(DOCS_DIR, "openapi_consultas.json")
    with open(openapi_path, "w", encoding="utf-8") as f:
        json.dump(exportar_openapi(), f, ensure_ascii=False, indent=2)
    print(f"✅ OpenAPI escrito en {openapi_path}")

    postman_path = os.path.join(DOCS_DIR, "postman_consultas.json")
    with open(postman_path, "w", encoding="utf-8") as f:
        json.dump(construir_postman(), f, ensure_ascii=False, indent=2)
    print(f"✅ Colección Postman escrita en {postman_path}")


if __name__ == "__main__":
    main()
