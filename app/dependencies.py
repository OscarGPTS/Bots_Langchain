"""Dependencias y singletons para la API."""
from typing import Optional

from app.core.logging import get_logger
from app.services.rag_simple import BotDocumentos
from app.services.rag_avanzado import BotDocumentosAvanzado

logger = get_logger(__name__)

_bot_simple: Optional[BotDocumentos] = None
_bot_avanzado: Optional[BotDocumentosAvanzado] = None


def get_bot_simple() -> BotDocumentos:
    """Obtener instancia singleton del bot simple."""
    global _bot_simple

    if _bot_simple is None:
        logger.info("Inicializando Bot Simple")
        _bot_simple = BotDocumentos()

    return _bot_simple


def get_bot_avanzado() -> BotDocumentosAvanzado:
    """Obtener instancia singleton del bot avanzado."""
    global _bot_avanzado

    if _bot_avanzado is None:
        logger.info("Inicializando Bot Avanzado")
        _bot_avanzado = BotDocumentosAvanzado()

    return _bot_avanzado


def reset_bots():
    """Resetear bots para recargar configuración."""
    global _bot_simple, _bot_avanzado
    _bot_simple = None
    _bot_avanzado = None
    logger.info("Bots reseteados")
