"""
Script de prueba para el Bot de Documentos Avanzado
====================================================
Prueba las funcionalidades de ChromaDB y OpenAI/Ollama
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots.bot_documentos_avanzado import BotDocumentosAvanzado


def main():
    """Ejecutar pruebas del bot avanzado"""
    
    print("="*70)
    print("🧪 PRUEBA DEL BOT DE DOCUMENTOS AVANZADO")
    print("="*70)
    
    try:
        # Inicializar bot
        print("\n1️⃣ Inicializando bot...")
        bot = BotDocumentosAvanzado()
        
        print("\n" + "="*70)
        print("2️⃣ PRUEBAS DE CONSULTA RÁPIDA")
        print("="*70)
        
        # Prueba 1: Consulta simple
        print("\n📝 Prueba 1: Consulta simple")
        pregunta1 = "¿Qué dice el código de ética sobre integridad?"
        print(f"Pregunta: {pregunta1}")
        respuesta1, stats1 = bot.consulta_rapida(pregunta1)
        print(f"\nRespuesta:\n{respuesta1[:500]}...")
        
        # Prueba 2: Búsqueda específica
        print("\n" + "-"*70)
        print("\n📝 Prueba 2: Búsqueda específica")
        pregunta2 = "¿Cuántos usuarios hay en el documento?"
        print(f"Pregunta: {pregunta2}")
        respuesta2, stats2 = bot.consulta_rapida(pregunta2)
        print(f"\nRespuesta:\n{respuesta2[:500]}...")
        
        print("\n" + "="*70)
        print("3️⃣ PRUEBAS DE RAZONAMIENTO PROFUNDO")
        print("="*70)
        
        # Prueba 3: Análisis complejo
        print("\n📝 Prueba 3: Análisis de documentos")
        pregunta3 = "Analiza y compara los documentos disponibles"
        print(f"Pregunta: {pregunta3}")
        respuesta3, stats3 = bot.razonamiento_profundo(pregunta3)
        print(f"\nRespuesta:\n{respuesta3[:700]}...")
        
        print("\n" + "="*70)
        print("4️⃣ PRUEBA DE DETECCIÓN AUTOMÁTICA")
        print("="*70)
        
        # Prueba 4: El bot decide el modo
        print("\n📝 Prueba 4: Modo automático")
        pregunta4 = "¿Qué información importante contienen estos documentos?"
        print(f"Pregunta: {pregunta4}")
        respuesta4 = bot.procesar(pregunta4)
        print(f"\nRespuesta:\n{respuesta4[:500]}...")
        
        print("\n" + "="*70)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*70)
        
        print("""
💡 SIGUIENTE PASO:
   
   Para usar el bot interactivo:
   python bots/bot_documentos_avanzado.py
   
   Para cambiar a OpenAI:
   1. Edita .env: LOCALIA=false
   2. Agrega: OPENAI_API_KEY=tu_clave
   3. Ejecuta de nuevo
""")
    
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
