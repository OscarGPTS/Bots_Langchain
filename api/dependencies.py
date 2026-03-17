"""Dependencias y singletons para la API"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bots.bot_documentos import BotDocumentos
from bots.bot_documentos_avanzado import BotDocumentosAvanzado
from typing import Optional

_bot_simple: Optional[BotDocumentos] = None
_bot_avanzado: Optional[BotDocumentosAvanzado] = None


def get_bot_simple() -> BotDocumentos:
    """Obtener instancia singleton del bot simple"""
    global _bot_simple
    
    if _bot_simple is None:
        print("[INFO] Inicializando Bot Simple")
        _bot_simple = BotDocumentos()
    
    return _bot_simple


def get_bot_avanzado() -> BotDocumentosAvanzado:
    """Obtener instancia singleton del bot avanzado"""
    global _bot_avanzado
    
    if _bot_avanzado is None:
        print("[INFO] Inicializando Bot Avanzado")
        _bot_avanzado = BotDocumentosAvanzado()
    
    return _bot_avanzado


def reset_bots():
    """Resetear bots para recargar configuración"""
    global _bot_simple, _bot_avanzado
    _bot_simple = None
    _bot_avanzado = None
    print("[INFO] Bots reseteados")
