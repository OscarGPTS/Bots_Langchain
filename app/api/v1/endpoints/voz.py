"""Rutas API para el servicio de voz (STT + RAG + TTS, local u OpenAI)."""
import base64
import io
import os
from enum import Enum
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas import VozResponse, VozHealthResponse
from app.services import voz as voz_service

router = APIRouter(prefix="/api/v1/voz", tags=["Voz"])

# Tamaño máximo del audio (defensa básica). Nginx ya limita a 50M en producción.
_MAX_BYTES = 25 * 1024 * 1024


class FormatoRespuesta(str, Enum):
    texto = "texto"
    audio = "audio"
    ambos = "ambos"


@router.post(
    "/consulta",
    response_model=VozResponse,
    summary="Consulta por voz (audio -> RAG -> texto/voz)",
    responses={
        200: {
            "description": (
                "Según `formato_respuesta`: `texto`/`ambos` devuelven JSON (VozResponse); "
                "`audio` devuelve el WAV directamente."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "pregunta_transcrita": "¿Cuál es el horario de trabajo?",
                        "respuesta": "El horario es de lunes a viernes de 8:00 a 17:00...",
                        "audio_base64": "UklGRiQAAABXQVZF...(base64)...",
                        "tiempo_respuesta": 5.8,
                    }
                },
                "audio/wav": {"schema": {"type": "string", "format": "binary"}},
            },
        },
        503: {"description": "Módulo de voz deshabilitado o dependencias faltantes"},
        413: {"description": "Audio demasiado grande"},
        422: {"description": "Audio vacío o ininteligible"},
    },
)
async def consulta_voz(
    file: UploadFile = File(..., description="Archivo de audio (webm/wav/mp3/ogg/m4a)"),
    formato_respuesta: FormatoRespuesta = Form(
        FormatoRespuesta.ambos, description="Formato de la respuesta: texto | audio | ambos"
    ),
):
    """Recibe audio, lo transcribe (STT), consulta el RAG y responde en texto y/o voz.

    **Flujo:** audio → STT (faster-whisper o OpenAI) → RAG existente → TTS (Piper u OpenAI).

    **Formatos de respuesta:**
    - `texto` → JSON `VozResponse` con `audio_base64: null`.
    - `audio` → `audio/wav` binario (header `X-Pregunta-Transcrita`).
    - `ambos` → JSON `VozResponse` con texto + `audio_base64`.

    **Requisitos:** `VOICE_ENABLED=true`. Proveedor local necesita `ffmpeg` y modelos
    descargados (`scripts/descargar_modelos_voz.py`); proveedor `openai` necesita `OPENAI_API_KEY`.
    """
    if not settings.VOICE_ENABLED:
        raise HTTPException(status_code=503, detail="Módulo de voz deshabilitado (VOICE_ENABLED=false).")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Archivo de audio vacío.")
    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado grande.")

    sufijo = os.path.splitext(file.filename or "")[1] or ".bin"

    try:
        resultado = voz_service.consulta_voz(audio_bytes, sufijo, formato_respuesta.value)
    except (RuntimeError, ValueError) as e:
        code = 422 if isinstance(e, ValueError) else 503
        raise HTTPException(status_code=code, detail=str(e))

    if formato_respuesta == FormatoRespuesta.audio:
        # Los headers HTTP son latin-1: percent-encode la transcripción (el cliente
        # debe aplicar decodeURIComponent / urllib.parse.unquote).
        return StreamingResponse(
            io.BytesIO(resultado["audio"]),
            media_type="audio/wav",
            headers={"X-Pregunta-Transcrita": quote(resultado["pregunta_transcrita"])},
        )

    audio_b64 = (
        base64.b64encode(resultado["audio"]).decode()
        if resultado.get("audio")
        else None
    )
    return VozResponse(
        pregunta_transcrita=resultado["pregunta_transcrita"],
        respuesta=resultado["respuesta"],
        audio_base64=audio_b64,
        tiempo_respuesta=resultado["tiempo_respuesta"],
    )


@router.get("/health", response_model=VozHealthResponse, summary="Estado del módulo de voz")
async def health():
    """Reporta proveedores activos y disponibilidad de ffmpeg, faster-whisper, Piper y OpenAI."""
    return VozHealthResponse(**voz_service.estado())
