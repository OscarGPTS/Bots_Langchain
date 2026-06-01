"""Cliente STT (Speech-to-Text) local con faster-whisper.

Carga perezosa: el modelo Whisper solo se carga en RAM en la primera transcripción
(no al arrancar la app), para no multiplicar memoria entre los workers de Gunicorn.
Las dependencias pesadas (faster_whisper) se importan dentro de las funciones para
que la app pueda importarse aunque no estén instaladas.
"""
import os
import shutil
import subprocess
import tempfile

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model = None  # singleton del modelo Whisper por worker


def _ffmpeg_exe() -> str | None:
    """Resolver el ejecutable de ffmpeg: PATH del sistema o fallback imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def ffmpeg_disponible() -> bool:
    return _ffmpeg_exe() is not None


def faster_whisper_disponible() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def _get_model():
    """Cargar (una vez) el modelo faster-whisper."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Cargando modelo Whisper '%s' (device=%s, compute=%s)...",
            settings.WHISPER_MODEL,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _model


def _normalizar_a_wav(origen: str) -> str:
    """Convertir cualquier audio de entrada a WAV 16 kHz mono con ffmpeg."""
    destino = origen + ".norm.wav"
    exe = _ffmpeg_exe()
    if not exe:
        raise RuntimeError("ffmpeg no está disponible en el sistema.")
    cmd = [
        exe, "-y", "-i", origen,
        "-ar", "16000", "-ac", "1", "-f", "wav", destino,
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {proc.stderr.decode(errors='ignore')[:300]}")
    return destino


def transcribir(audio_bytes: bytes, sufijo: str = ".bin") -> str:
    """Transcribir audio a texto. Devuelve la transcripción en texto plano."""
    if not faster_whisper_disponible():
        raise RuntimeError("faster-whisper no está instalado (pip install faster-whisper).")
    if not ffmpeg_disponible():
        raise RuntimeError("ffmpeg no está disponible en el sistema.")

    tmp_in = None
    tmp_wav = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as f:
            f.write(audio_bytes)
            tmp_in = f.name

        tmp_wav = _normalizar_a_wav(tmp_in)

        model = _get_model()
        segments, _info = model.transcribe(tmp_wav, language=settings.STT_LANGUAGE)
        texto = "".join(seg.text for seg in segments).strip()
        return texto
    finally:
        for p in (tmp_in, tmp_wav):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
