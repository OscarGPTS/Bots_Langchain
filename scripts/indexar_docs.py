"""Indexación manual de documentos de Paperless en ChromaDB.

Mecanismo oficial de indexación (fuera del arranque de la API). Indexa tanto la
colección del bot simple como la del bot avanzado.

Uso:
    python scripts/indexar_docs.py            # ambos bots
    python scripts/indexar_docs.py simple     # solo bot simple
    python scripts/indexar_docs.py avanzado   # solo bot avanzado
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_simple import BotDocumentos
from app.services.rag_avanzado import BotDocumentosAvanzado


def indexar_simple():
    print("\n" + "=" * 70)
    print("🔧 Indexando colección del BOT SIMPLE (docs_simple)")
    print("=" * 70)
    bot = BotDocumentos()
    bot._cargar_documentos()
    print(f"📊 Documentos indexados: {len(bot.documentos_indexados)}")
    if bot.vector_store:
        print(f"📊 Vectores en ChromaDB: {bot.vector_store._collection.count()}")


def indexar_avanzado():
    print("\n" + "=" * 70)
    print("🔧 Indexando colección del BOT AVANZADO")
    print("=" * 70)
    bot = BotDocumentosAvanzado()
    bot._cargar_documentos_paperless()
    print(f"📊 Documentos indexados: {len(bot.documentos_indexados)}")
    if bot.vector_store:
        print(f"📊 Vectores en ChromaDB: {bot.vector_store._collection.count()}")


def main():
    objetivo = sys.argv[1].lower() if len(sys.argv) > 1 else "ambos"

    if objetivo in ("simple", "ambos"):
        indexar_simple()
    if objetivo in ("avanzado", "ambos"):
        indexar_avanzado()

    print("\n" + "=" * 70)
    print("✅ INDEXACIÓN COMPLETADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
