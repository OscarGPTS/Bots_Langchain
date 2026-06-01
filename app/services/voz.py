"""Servicio de voz: orquesta STT -> RAG existente -> TTS.

No reimplementa lógica RAG: reutiliza los bots existentes (simple o avanzado)
según `VOICE_BACKEND`.
"""
import re
import time

from app.clients import stt, tts
from app.core.config import settings
from app.core.logging import get_logger
from app.dependencies import get_bot_simple, get_bot_avanzado

logger = get_logger(__name__)


def _responder_rag(pregunta: str) -> str:
    """Obtener respuesta del bot RAG configurado."""
    if settings.VOICE_BACKEND == "avanzado":
        bot = get_bot_avanzado()
        respuesta, _stats = bot.consulta_rapida(pregunta, None)
        return respuesta
    bot = get_bot_simple()
    return bot.procesar(pregunta)


def _limpiar_para_voz(texto: str) -> str:
    """Preparar el texto para TTS: quitar la sección de fuentes y los emojis/separadores."""
    # Cortar en el separador de "Documentos consultados/analizados"
    corte = re.split(r"[─]{3,}", texto)[0]
    # Quitar emojis y símbolos comunes del formateo
    limpio = re.sub(r"[🤖📚📄📅🔗🏷️✅⚠️❌💡🔍🔧📖📥🗄️🚀📊]", "", corte)
    limpio = limpio.replace("ID:", "")
    return limpio.strip()


def consulta_voz(audio_bytes: bytes, sufijo: str, formato_respuesta: str = "ambos") -> dict:
    """Procesar una consulta por voz.

    Devuelve un dict con: pregunta_transcrita, respuesta (texto), audio (bytes|None),
    tiempo_respuesta.
    """
    inicio = time.time()

    pregunta = stt.transcribir(audio_bytes, sufijo=sufijo)
    if not pregunta:
        raise ValueError("No se pudo transcribir audio (vacío o ininteligible).")

    logger.info("Voz transcrita: %r", pregunta)
    respuesta = _responder_rag(pregunta)

    audio = None
    if formato_respuesta in ("audio", "ambos"):
        audio = tts.sintetizar(_limpiar_para_voz(respuesta))

    return {
        "pregunta_transcrita": pregunta,
        "respuesta": respuesta,
        "audio": audio,
        "tiempo_respuesta": round(time.time() - inicio, 2),
    }


def estado() -> dict:
    """Estado de los componentes de voz (para health)."""
    return {
        "voice_enabled": settings.VOICE_ENABLED,
        "stt_provider": settings.STT_PROVIDER,
        "tts_provider": settings.TTS_PROVIDER,
        "ffmpeg_disponible": stt.ffmpeg_disponible(),
        "faster_whisper_disponible": stt.faster_whisper_disponible(),
        "piper_disponible": tts.piper_disponible(),
        "voz_piper_existe": tts.voz_existe(),
        "openai_disponible": stt.openai_disponible(),
        "backend_rag": settings.VOICE_BACKEND,
        "whisper_model": settings.WHISPER_MODEL,
    }
