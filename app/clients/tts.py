"""Cliente TTS (Text-to-Speech) local con Piper.

Carga perezosa de la voz. Las dependencias se importan dentro de las funciones
para que la app pueda importarse aunque Piper no esté instalado.
"""
import io
import os
import wave

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_voice = None  # singleton de la voz Piper por worker


def piper_disponible() -> bool:
    try:
        import piper  # noqa: F401
        return True
    except Exception:
        return False


def voz_existe() -> bool:
    return os.path.exists(settings.PIPER_VOICE_PATH)


def _get_voice():
    """Cargar (una vez) la voz Piper desde el .onnx configurado."""
    global _voice
    if _voice is None:
        from piper import PiperVoice

        if not voz_existe():
            raise RuntimeError(
                f"No se encontró la voz Piper en {settings.PIPER_VOICE_PATH}. "
                "Ejecuta scripts/descargar_modelos_voz.py."
            )
        logger.info("Cargando voz Piper: %s", settings.PIPER_VOICE_PATH)
        _voice = PiperVoice.load(settings.PIPER_VOICE_PATH)
    return _voice


def sintetizar(texto: str) -> bytes:
    """Sintetizar texto a audio WAV (bytes)."""
    if not piper_disponible():
        raise RuntimeError("piper-tts no está instalado (pip install piper-tts).")
    if not texto.strip():
        raise ValueError("Texto vacío para sintetizar.")

    voice = _get_voice()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        # synthesize_wav configura el formato del wav (canales, sample rate, etc.).
        voice.synthesize_wav(texto, wav_file, set_wav_format=True)
    return buffer.getvalue()
