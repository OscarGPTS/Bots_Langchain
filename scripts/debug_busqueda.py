"""
Script de depuración para entender el problema de búsqueda
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots.bot_documentos import BotDocumentos


def debug_busqueda():
    """Depurar el problema de búsqueda"""
    
    bot = BotDocumentos()
    
    print("=" * 70)
    print("🔍 DEBUG - BÚSQUEDA DE DOCUMENTOS")
    print("=" * 70)
    
    # Test 1: Buscar con query vacía (debe listar todos)
    print("\n1️⃣ Búsqueda sin query (listar todos):")
    docs = bot.buscar_documentos("")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 2: Buscar "código"
    print("\n2️⃣ Búsqueda: 'código'")
    docs = bot.buscar_documentos("código")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 3: Buscar "ética"
    print("\n3️⃣ Búsqueda: 'ética'")
    docs = bot.buscar_documentos("ética")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 4: Buscar "codigo" (sin tilde)
    print("\n4️⃣ Búsqueda: 'codigo' (sin tilde)")
    docs = bot.buscar_documentos("codigo")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 5: Buscar "etica" (sin tilde)
    print("\n5️⃣ Búsqueda: 'etica' (sin tilde)")
    docs = bot.buscar_documentos("etica")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 6: Buscar "usuarios"
    print("\n6️⃣ Búsqueda: 'usuarios'")
    docs = bot.buscar_documentos("usuarios")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    # Test 7: Buscar "GPT"
    print("\n7️⃣ Búsqueda: 'GPT'")
    docs = bot.buscar_documentos("GPT")
    print(f"   Encontrados: {len(docs)}")
    for doc in docs:
        print(f"   - {doc.get('title')} (ID: {doc.get('id')})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    debug_busqueda()
