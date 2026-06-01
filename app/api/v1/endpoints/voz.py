"""Rutas API para el servicio de voz (STT + RAG + TTS local)."""
import base64
import io
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas import VozResponse, VozTextoResponse, VozHealthResponse
from app.services import voz as voz_service

router = APIRouter(prefix="/api/v1/voz", tags=["Voz"])

# Tamaño máximo del audio (defensa básica). Nginx ya limita a 50M en producción.
_MAX_BYTES = 25 * 1024 * 1024


@router.post("/consulta", summary="Consulta por voz (audio -> RAG -> texto/voz)")
async def consulta_voz(
    file: UploadFile = File(..., description="Archivo de audio (webm/wav/mp3/ogg/m4a)"),
    formato_respuesta: str = Form("ambos", description="texto | audio | ambos"),
):
    """Recibe audio, lo transcribe, consulta el RAG y responde en texto y/o voz.

    - `texto`  → JSON `VozTextoResponse`
    - `audio`  → `audio/wav` (header `X-Pregunta-Transcrita`)
    - `ambos`  → JSON `VozResponse` (texto + `audio_base64`)
    """
    if not settings.VOICE_ENABLED:
        raise HTTPException(status_code=503, detail="Módulo de voz deshabilitado (VOICE_ENABLED=false).")

    if formato_respuesta not in ("texto", "audio", "ambos"):
        raise HTTPException(status_code=422, detail="formato_respuesta debe ser: texto | audio | ambos")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Archivo de audio vacío.")
    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado grande.")

    sufijo = os.path.splitext(file.filename or "")[1] or ".bin"

    try:
        resultado = voz_service.consulta_voz(audio_bytes, sufijo, formato_respuesta)
    except (RuntimeError, ValueError) as e:
        # Errores esperados (deps faltantes, audio inválido): 503/422
        code = 422 if isinstance(e, ValueError) else 503
        raise HTTPException(status_code=code, detail=str(e))

    if formato_respuesta == "audio":
        return StreamingResponse(
            io.BytesIO(resultado["audio"]),
            media_type="audio/wav",
            headers={"X-Pregunta-Transcrita": resultado["pregunta_transcrita"]},
        )

    if formato_respuesta == "texto":
        return VozTextoResponse(
            pregunta_transcrita=resultado["pregunta_transcrita"],
            respuesta=resultado["respuesta"],
            tiempo_respuesta=resultado["tiempo_respuesta"],
        )

    # ambos
    audio_b64 = base64.b64encode(resultado["audio"]).decode() if resultado["audio"] else None
    return VozResponse(
        pregunta_transcrita=resultado["pregunta_transcrita"],
        respuesta=resultado["respuesta"],
        audio_base64=audio_b64,
        tiempo_respuesta=resultado["tiempo_respuesta"],
    )


@router.get("/health", response_model=VozHealthResponse, summary="Estado del módulo de voz")
async def health():
    """Reporta disponibilidad de ffmpeg, faster-whisper, Piper y la voz configurada."""
    return VozHealthResponse(**voz_service.estado())
