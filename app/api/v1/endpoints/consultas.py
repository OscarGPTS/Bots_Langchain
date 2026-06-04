"""Rutas API del módulo de Consultas a Datos (NL -> SQL / API REST, solo lectura)."""
import requests
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.consultas import ConsultaRequest, ConsultaResponse, ConsultasHealthResponse
from app.services.consultas import orquestador
from app.services.consultas.orquestador import ConsultaError

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/consultas", tags=["Consultas"])


@router.post(
    "/",
    response_model=ConsultaResponse,
    summary="Consultar datos de un origen (texto -> SQL/API, solo lectura)",
    responses={
        200: {"description": "Objeto estructurado (texto/tabla)."},
        400: {"description": "Origen inexistente, consulta inválida o SQL no permitido."},
        503: {"description": "Módulo deshabilitado o error de conexión con el origen."},
    },
)
async def consultar(request: ConsultaRequest):
    """Recibe lo que pide el usuario y el `origen`, y devuelve datos estructurados.

    **Flujo:** keys → acota tablas/recursos → el LLM genera un `SELECT` (validado
    como solo-lectura) o elige un endpoint REST `GET` → ejecuta → objeto estructurado.

    **Seguridad:** solo lectura. SQL validado (sqlglot) + usuario MySQL read-only;
    REST solo `GET` con allowlist de host y params. Ver `config/rules.example.yaml`.
    """
    try:
        formato = request.formato.value if request.formato else None
        return orquestador.procesar_consulta(request.consulta, request.origen, formato)
    except ConsultaError as e:
        # Errores de negocio/validación: 400 (deshabilitado -> 503).
        if "deshabilitado" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Validación de SQL / generación.
        raise HTTPException(status_code=400, detail=str(e))
    except (requests.RequestException, SQLAlchemyError) as e:
        logger.error("Error conectando con el origen: %s", e)
        raise HTTPException(status_code=503, detail="Error al consultar el origen de datos.")


@router.get("/health", response_model=ConsultasHealthResponse, summary="Estado del módulo de consultas")
async def health():
    """Reporta si el módulo está activo, si el catálogo cargó y los orígenes disponibles."""
    return ConsultasHealthResponse(**orquestador.estado())
