"""
Verificador de Ollama - Modelos Disponibles
============================================
Este script verifica qué modelos están disponibles en tu servidor Ollama.
Úsalo para configurar correctamente el bot híbrido de RH.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

OLLAMA_BASE_URL = os.getenv('OLLAMA_URL')

def verificar_ollama():
    """Verifica conexión y modelos disponibles en Ollama"""
    
    print("=" * 70)
    print("🔍 VERIFICADOR DE OLLAMA")
    print("=" * 70)
    print(f"\n📡 Servidor: {OLLAMA_BASE_URL}\n")
    
    # Probar conexión básica
    print("🧪 Probando conexión...")
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print("✅ Conexión exitosa\n")
            
            data = response.json()
            models = data.get('models', [])
            
            if not models:
                print("⚠️ No se encontraron modelos instalados\n")
                print("💡 Contacta a tu equipo de IT para instalar un modelo")
                print("   Modelos recomendados: llama3, mistral, phi\n")
                return
            
            print("=" * 70)
            print(f"📦 MODELOS DISPONIBLES ({len(models)} encontrados):")
            print("=" * 70)
            
            for i, model in enumerate(models, 1):
                name = model.get('name', 'N/A')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                modified = model.get('modified_at', 'N/A')
                
                print(f"\n{i}. {name}")
                print(f"   Tamaño: {size_gb:.2f} GB")
                print(f"   Modificado: {modified[:10]}")
            
            print("\n" + "=" * 70)
            print("⚙️ CONFIGURACIÓN RECOMENDADA:")
            print("=" * 70)
            
            # Recomendar el primer modelo
            if models:
                recommended = models[0].get('name', '')
                print(f"\nEn bot_empresa_rh_hibrido.py, línea 30, usa:\n")
                print(f'OLLAMA_MODEL = "{recommended}"')
                print("\nEjemplo completo:")
                print("-" * 70)
                print("USAR_IA = True")
                print(f'OLLAMA_BASE_URL = "{OLLAMA_BASE_URL}"')
                print(f'OLLAMA_MODEL = "{recommended}"')
                print("-" * 70)
            
            print("\n✅ Ollama está listo para usar")
            print("💡 Cambia USAR_IA = True en bot_empresa_rh_hibrido.py\n")
            
        elif response.status_code == 404:
            print("❌ Error 404: Endpoint no encontrado")
            print(f"💡 Verifica que la URL sea correcta: {OLLAMA_BASE_URL}")
            print("   Prueba: /api/tags, /api/version, etc.\n")
            
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}\n")
    
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El servidor no respondió a tiempo")
        print("💡 Verifica que Ollama esté corriendo\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor")
        print(f"💡 Verifica que la URL sea correcta: {OLLAMA_BASE_URL}")
        print("   Verifica tu conexión a red\n")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}\n")
    
    # Recomendaciones finales
    print("=" * 70)
    print("💡 RECOMENDACIONES:")
    print("=" * 70)
    print("\n🎯 Si Ollama funciona:")
    print("   1. Copia el OLLAMA_MODEL recomendado arriba")
    print("   2. Pégalo en bot_empresa_rh_hibrido.py línea 30")
    print("   3. Cambia USAR_IA = True (línea 26)")
    print("   4. Ejecuta: python bot_empresa_rh_hibrido.py")
    
    print("\n⚡ Si Ollama NO funciona o es muy lento:")
    print("   1. Cambia USAR_IA = False en bot_empresa_rh_hibrido.py")
    print("   2. El bot funcionará igual pero más rápido")
    print("   3. Solo usará búsqueda directa (sin IA)\n")

if __name__ == "__main__":
    verificar_ollama()
