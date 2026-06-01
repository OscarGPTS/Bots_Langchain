"""Descargar modelos de voz (STT/TTS) para el módulo local.

- faster-whisper: el modelo se descarga automáticamente al primer uso (cache en
  ~/.cache/huggingface). Aquí solo se fuerza la descarga del modelo configurado.
- Piper: descarga una voz en español (es_MX) a models/piper/.

Uso:
    python scripts/descargar_modelos_voz.py
"""
import sys
import urllib.request
from pathlib import Path

# La consola de Windows (cp1252) no puede imprimir emojis; forzar UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402

# Voz Piper por defecto (es_MX, femenina: "claude"). Cambiar por otra voz del repo
# si se prefiere: https://huggingface.co/rhasspy/piper-voices/tree/main/es
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high"
PIPER_FILES = {
    "es_MX.onnx": f"{PIPER_BASE}/es_MX-claude-high.onnx?download=true",
    "es_MX.onnx.json": f"{PIPER_BASE}/es_MX-claude-high.onnx.json?download=true",
}


def descargar_whisper():
    print(f"\n📥 Descargando modelo Whisper '{settings.WHISPER_MODEL}'...")
    try:
        from faster_whisper import WhisperModel

        WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
        print("✅ Modelo Whisper listo (en cache).")
    except ImportError:
        print("⚠️ faster-whisper no instalado: pip install faster-whisper")


def descargar_piper():
    destino_onnx = Path(settings.PIPER_VOICE_PATH)
    carpeta = destino_onnx.parent
    carpeta.mkdir(parents=True, exist_ok=True)

    print(f"\n📥 Descargando voz Piper (es_MX) a {carpeta}/ ...")
    # nombres de destino: <PIPER_VOICE_PATH> y <PIPER_VOICE_PATH>.json
    destinos = {
        destino_onnx.name: destino_onnx,
        destino_onnx.name + ".json": Path(str(destino_onnx) + ".json"),
    }
    urls = list(PIPER_FILES.values())
    for (nombre, ruta), url in zip(destinos.items(), urls):
        if ruta.exists():
            print(f"   • {ruta.name} ya existe, omitido.")
            continue
        print(f"   • Descargando {ruta.name} ...")
        urllib.request.urlretrieve(url, ruta)
    print("✅ Voz Piper lista.")


def main():
    descargar_whisper()
    try:
        descargar_piper()
    except Exception as e:
        print(f"⚠️ Error descargando voz Piper: {e}")
        print("   Descárgala manualmente desde https://huggingface.co/rhasspy/piper-voices/tree/main/es")
    print("\n✅ Listo. Recuerda instalar ffmpeg en el sistema (sudo apt install ffmpeg).")


if __name__ == "__main__":
    main()
