"""Voz para el módulo de consultas: STT -> orquestador -> (opcional) TTS.

Reutiliza los mismos clientes STT/TTS del servicio de voz existente. La consulta
hablada se transcribe, se procesa como una consulta normal (NL -> SQL / API REST,
solo lectura) y, opcionalmente, se devuelve un resumen hablado.
"""
import re

from app.clients import stt, tts
from app.core.logging import get_logger
from app.services.consultas import orquestador

logger = get_logger(__name__)


def _texto_para_voz(resultado) -> str:
    """Texto breve y hablable de la respuesta.

    Usa el resumen corto y ya personalizado (`resultado.texto`) que arma el
    formateador — NO dicta las filas de la tabla (sería enorme). Para tipo=tabla/
    grafico es una frase tipo "{nombre}, aquí tienes el resultado: N registros";
    para tipo=texto es la respuesta real a la pregunta.
    """
    crudo = resultado.texto or "Consulta procesada."
    # Quitar emojis/símbolos del formateo para que el TTS no los lea.
    return re.sub(r"[🤖📚📄📅🔗🏷️✅⚠️❌💡🔍🔧📖📥🗄️🚀📊─]", "", crudo).strip()


def consulta_voz(
    audio_bytes: bytes,
    sufijo: str,
    origen: str,
    formato: str | None,
    responder_voz: bool,
    usuario: str | None = None,
    objetivo: str | None = None,
) -> dict:
    """Procesar una consulta por voz.

    `usuario` personaliza la respuesta (hablada y en texto). `objetivo` acota la
    consulta a una tabla/recurso concreto. Devuelve dict con: pregunta_transcrita,
    resultado (ConsultaResponse), audio (bytes|None).
    Lanza ValueError (entrada inválida) o RuntimeError (dependencias de voz faltantes).
    """
    pregunta = stt.transcribir(audio_bytes, sufijo=sufijo)
    if not pregunta:
        raise ValueError("No se pudo transcribir audio (vacío o ininteligible).")

    logger.info("[consultas/voz] transcrito=%r origen=%s usuario=%s objetivo=%s", pregunta, origen, usuario, objetivo)
    resultado = orquestador.procesar_consulta(pregunta, origen, formato, usuario, objetivo)

    audio = None
    if responder_voz:
        audio = tts.sintetizar(_texto_para_voz(resultado))

    return {"pregunta_transcrita": pregunta, "resultado": resultado, "audio": audio}
