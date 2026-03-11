"""Test realista del bot"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.bot_documentos import BotDocumentos

bot = BotDocumentos()

# Simular consultas que un usuario haría
consultas = [
    "lista documentos recientes",
    "busca código de ética",
    "busca usuarios",
    "analiza documento 1",
    "¿Qué dice el código de ética sobre conducta?",
]

for i, consulta in enumerate(consultas, 1):
    print(f"\n{'='*60}")
    print(f"Prueba {i}: {consulta}")
    print('='*60)
    resultado = bot.procesar(consulta)
    print(resultado[:500])  # Solo primeros 500 caracteres
    print()
