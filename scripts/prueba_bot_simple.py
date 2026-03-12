"""Prueba simple del bot con ChromaDB"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bots.bot_documentos import BotDocumentos

print("="*70)
print("PRUEBA BOT DE DOCUMENTOS CON CHROMADB")
print("="*70)
print()

# Inicializar bot
bot = BotDocumentos()

print()
print("="*70)
print("CONSULTA: Cuales son las obligaciones de los empleados?")
print("="*70)
print()

# Hacer consulta
respuesta = bot.procesar("Cuales son las obligaciones de los empleados?")
print(respuesta)
