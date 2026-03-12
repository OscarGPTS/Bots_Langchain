"""Script para forzar indexación de documentos en docs_simple"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bots.bot_documentos import BotDocumentos

print("="*70)
print("🔧 FORZANDO INDEXACIÓN EN COLECCIÓN docs_simple")
print("="*70)
print()

bot = BotDocumentos()

print()
print("="*70)
print("✅ INDEXACIÓN COMPLETADA")
print("="*70)
print()
print(f"📊 Documentos indexados: {len(bot.documentos_indexados)}")
if bot.vector_store:
    count = bot.vector_store._collection.count()
    print(f"📊 Vectores en ChromaDB: {count}")
