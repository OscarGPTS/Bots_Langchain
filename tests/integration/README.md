# Tests de integración (legacy)

Estos archivos provienen de la antigua carpeta `scripts/` y son **scripts manuales**
que requieren servicios externos en vivo (Paperless, Ollama y/o OpenAI). No se
ejecutan en la corrida por defecto de `pytest` (ver `testpaths` en `pyproject.toml`).

Para ejecutarlos manualmente:

```bash
python -m tests.integration.test_api_cliente
# o el script que corresponda
```

> Pendiente: convertir progresivamente a tests `pytest` reales con fixtures y mocks
> de los clientes externos (`app/clients/`).
