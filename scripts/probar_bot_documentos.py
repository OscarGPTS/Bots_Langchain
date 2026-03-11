"""
Script de prueba automática para el bot de documentos.
Ejecuta varias consultas de prueba para verificar el funcionamiento.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots.bot_documentos import BotDocumentos


def imprimir_separador(titulo=""):
    """Imprime un separador visual"""
    print("\n" + "="*70)
    if titulo:
        print(f"🧪 {titulo}")
        print("="*70)


def probar_bot():
    """Ejecuta pruebas automáticas del bot de documentos"""
    
    print("="*70)
    print("🤖 PRUEBA AUTOMÁTICA DEL BOT DE DOCUMENTOS")
    print("="*70)
    
    # Inicializar el bot
    print("\n📦 Inicializando bot...")
    bot = BotDocumentos()
    print("✅ Bot inicializado correctamente")
    
    # Lista de consultas de prueba
    consultas_prueba = [
        ("Lista de documentos", "lista documentos recientes"),
        ("Búsqueda: Código de Ética", "busca código de ética"),
        ("Búsqueda: Usuarios", "busca usuarios"),
        ("Análisis documento 1", "analiza documento 1"),
        ("Pregunta sobre contenido", "¿Qué dice el código de ética sobre conducta?"),
    ]
    
    # Ejecutar cada prueba
    for i, (descripcion, consulta) in enumerate(consultas_prueba, 1):
        imprimir_separador(f"PRUEBA {i}: {descripcion}")
        print(f"📝 Consulta: {consulta}\n")
        
        try:
            respuesta = bot.procesar(consulta)
            print(f"🤖 Respuesta:\n{respuesta}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        print("\n✅ Prueba completada")
    
    # Resumen final
    imprimir_separador("PRUEBAS COMPLETADAS")
    print("✅ Todas las pruebas han sido ejecutadas")
    print("\n💡 Siguiente paso: Prueba el bot interactivo con:")
    print("   python bots/bot_documentos.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        probar_bot()
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error general: {str(e)}")
        import traceback
        print(traceback.format_exc())
