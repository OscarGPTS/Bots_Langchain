"""Rutas API del módulo de Consultas a Datos (NL -> SQL / API REST, solo lectura)."""
import base64
import os

import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.consultas import (
    ConsultaRequest,
    ConsultaResponse,
    ConsultasHealthResponse,
    ConsultaVozResponse,
)
from app.services.consultas import orquestador
from app.services.consultas import voz as consultas_voz
from app.services.consultas.orquestador import ConsultaError

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/consultas", tags=["Consultas"])

# Tamaño máximo del audio aceptado (Nginx ya limita a 50M en producción).
_MAX_AUDIO_BYTES = 25 * 1024 * 1024


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
        return orquestador.procesar_consulta(
            request.consulta, request.origen, formato, request.usuario, request.objetivo
        )
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


@router.post(
    "/voz",
    response_model=ConsultaVozResponse,
    summary="Consultar datos por voz (audio -> transcripción -> SQL/API -> objeto + voz)",
    responses={
        200: {"description": "Transcripción + objeto estructurado (+ resumen hablado opcional)."},
        400: {"description": "Origen inexistente / consulta inválida / SQL no permitido."},
        413: {"description": "Audio demasiado grande."},
        422: {"description": "Audio vacío o ininteligible."},
        503: {"description": "Módulo de consultas o de voz deshabilitado / dependencias faltantes."},
    },
)
async def consultar_voz(
    file: UploadFile = File(..., description="Archivo de audio (webm/wav/mp3/ogg/m4a)"),
    origen: str = Form(..., description="Clave del origen a consultar (p.ej. cartera_db, rh_api)"),
    formato: str | None = Form(None, description="Fuerza la salida: texto | tabla | grafico | informe"),
    responder_voz: bool = Form(True, description="Si true, incluye un resumen hablado (audio_base64)"),
    usuario: str | None = Form(None, description="Nombre de quien consulta, para personalizar la respuesta"),
    objetivo: str | None = Form(None, description="Tabla/recurso específico a consultar (omite el matcher)"),
):
    """Recibe audio, lo transcribe (STT) y lo procesa como una consulta a datos.

    **Flujo:** audio → STT (faster-whisper u OpenAI) → orquestador (NL→SQL/API,
    solo lectura) → objeto estructurado + (opcional) resumen hablado (TTS).

    Reutiliza la misma configuración de voz del módulo `/api/v1/voz`
    (`VOICE_ENABLED`, `STT_PROVIDER`, `TTS_PROVIDER`, …) y de consultas
    (`CONSULTAS_ENABLED`, catálogo de reglas).
    """
    if not settings.CONSULTAS_ENABLED:
        raise HTTPException(status_code=503, detail="El módulo de consultas está deshabilitado (CONSULTAS_ENABLED=false).")
    if not settings.VOICE_ENABLED:
        raise HTTPException(status_code=503, detail="Módulo de voz deshabilitado (VOICE_ENABLED=false).")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Archivo de audio vacío.")
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado grande.")

    sufijo = os.path.splitext(file.filename or "")[1] or ".bin"

    try:
        res = consultas_voz.consulta_voz(audio_bytes, sufijo, origen, formato, responder_voz, usuario, objetivo)
    except ConsultaError as e:
        code = 503 if "deshabilitado" in str(e) else 400
        raise HTTPException(status_code=code, detail=str(e))
    except ValueError as e:
        # ValueError abarca audio ininteligible (422) y SQL/consulta inválida (400).
        raise HTTPException(status_code=422 if "transcribir" in str(e) else 400, detail=str(e))
    except RuntimeError as e:
        # Dependencias de voz faltantes (ffmpeg/whisper/piper) u OpenAI no disponible.
        raise HTTPException(status_code=503, detail=str(e))
    except (requests.RequestException, SQLAlchemyError) as e:
        logger.error("Error conectando con el origen: %s", e)
        raise HTTPException(status_code=503, detail="Error al consultar el origen de datos.")

    audio_b64 = base64.b64encode(res["audio"]).decode() if res.get("audio") else None
    return ConsultaVozResponse(
        pregunta_transcrita=res["pregunta_transcrita"],
        resultado=res["resultado"],
        audio_base64=audio_b64,
    )


@router.get("/health", response_model=ConsultasHealthResponse, summary="Estado del módulo de consultas")
async def health():
    """Reporta si el módulo está activo, si el catálogo cargó y los orígenes disponibles."""
    return ConsultasHealthResponse(**orquestador.estado())
