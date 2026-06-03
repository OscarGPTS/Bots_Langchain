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
    """Resolver el ejecutable de ffmpeg.

    Orden: PATH del proceso → rutas absolutas conocidas (útil cuando systemd
    restringe PATH al venv) → fallback imageio-ffmpeg (dev Windows).
    """
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    for candidate in ("/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/bin/ffmpeg"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            logger.debug("ffmpeg encontrado por ruta absoluta: %s", candidate)
            return candidate
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


def openai_disponible() -> bool:
    if not settings.OPENAI_API_KEY:
        return False
    try:
        import openai  # noqa: F401
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
    """Transcribir audio a texto según STT_PROVIDER (local | openai)."""
    if settings.STT_PROVIDER == "openai":
        return _transcribir_openai(audio_bytes, sufijo)
    return _transcribir_local(audio_bytes, sufijo)


def _transcribir_local(audio_bytes: bytes, sufijo: str) -> str:
    """STT con faster-whisper (local)."""
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


def _transcribir_openai(audio_bytes: bytes, sufijo: str) -> str:
    """STT con la API de OpenAI (whisper-1 / gpt-4o-transcribe).

    No requiere ffmpeg: OpenAI acepta webm/mp3/wav/m4a directamente.
    """
    if not openai_disponible():
        raise RuntimeError("OpenAI no disponible (falta OPENAI_API_KEY o paquete openai).")

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    tmp_in = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo or ".webm") as f:
            f.write(audio_bytes)
            tmp_in = f.name

        with open(tmp_in, "rb") as audio_file:
            resp = client.audio.transcriptions.create(
                model=settings.OPENAI_STT_MODEL,
                file=audio_file,
                language=settings.STT_LANGUAGE,
            )
        return (resp.text or "").strip()
    finally:
        if tmp_in and os.path.exists(tmp_in):
            try:
                os.remove(tmp_in)
            except OSError:
                pass
