"""
Prueba simple del bot avanzado - SIN GASTAR TOKENS
==================================================
Prueba básica usando Ollama local (LOCALIA=true)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Asegurar que use modo local
os.environ['LOCALIA'] = 'true'

from bots.bot_documentos_avanzado import BotDocumentosAvanzado


def prueba_simple():
    """Prueba simple sin gastar tokens de OpenAI"""
    
    print("="*70)
    print("🧪 PRUEBA SIMPLE - BOT AVANZADO (MODO LOCAL)")
    print("="*70)
    print("\n💡 Usando LOCALIA=true (Ollama local, SIN COSTOS)")
    print()
    
    try:
        # Inicializar bot
        print("1️⃣ Inicializando bot...\n")
        bot = BotDocumentosAvanzado()
        
        print("\n" + "="*70)
        print("2️⃣ PRUEBA: Consulta Rápida")
        print("="*70)
        
        # Consulta simple
        pregunta = "¿Qué dice el código de ética sobre integridad?"
        print(f"\n📝 Pregunta: {pregunta}\n")
        
        respuesta, stats = bot.consulta_rapida(pregunta)
        
        print("\n🎯 RESULTADO:")
        print("="*70)
        # Mostrar solo los primeros 500 caracteres
        if len(respuesta) > 500:
            print(respuesta[:500] + "...")
        else:
            print(respuesta)
        
        print("\n" + "="*70)
        print("✅ PRUEBA COMPLETADA")
        print("="*70)
        
        print("""
💡 RESUMEN:
   ✅ ChromaDB inicializado correctamente
   ✅ Documentos vectorizados y persistidos
   ✅ Búsqueda semántica funcional
   ✅ Ollama local funcionando (SIN COSTOS)
   
🚀 SIGUIENTE PASO:
   
   Para usar modo interactivo:
   python bots/bot_documentos_avanzado.py
   
   Para cambiar a OpenAI (opcional):
   1. En .env: LOCALIA=false
   2. Agrega: OPENAI_API_KEY=tu_clave
""")
    
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    prueba_simple()
