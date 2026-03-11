"""Test rápido de búsqueda"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.bot_documentos import BotDocumentos

bot = BotDocumentos()

tests = [
    ("código", "Búsqueda con 'código'"),
    ("código de ética", "Búsqueda con 'código de ética'"),
    ("ética", "Búsqueda con 'ética'"),
    ("usuarios", "Búsqueda con 'usuarios'"),
]

for query, descripcion in tests:
    print(f"\n{descripcion}:")
    docs = bot.buscar_documentos(query)
    print(f"  Encontrados: {len(docs)}")
    for d in docs:
        print(f"  - {d.get('title')}")
