"""Test del problema reportado"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.bot_documentos import BotDocumentos

bot = BotDocumentos()

print("="*60)
print("TEST: codigo de etica punto 4.19")
print("="*60)

# Test 1: Query problemática
print("\n1. Query completa:")
consulta = "codigo de etica punto 4.19"
resultado = bot.procesar(consulta)
print(resultado[:500])

# Test 2: Búsqueda directa
print("\n2. Búsqueda directa con query completa:")
docs = bot.buscar_documentos("codigo de etica punto 4.19")
print(f"   Encontrados: {len(docs)}")

# Test 3: Búsqueda solo con "codigo de etica"
print("\n3. Búsqueda solo con 'codigo de etica':")
docs = bot.buscar_documentos("codigo de etica")
print(f"   Encontrados: {len(docs)}")
for d in docs:
    print(f"   - {d.get('title')}")

# Test 4: Que la IA analice el documento 1 buscando punto 4.19
print("\n4. Análisis directo del documento 1:")
resultado = bot.analizar_documento(1, "¿Qué dice el punto 4.19?")
print(resultado[:500])
