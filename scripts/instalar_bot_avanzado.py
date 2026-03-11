"""
Script de instalación de dependencias para el Bot Avanzado
===========================================================
Instala ChromaDB y dependencias adicionales necesarias
"""

import subprocess
import sys


def instalar_dependencias():
    """Instalar dependencias del bot avanzado"""
    
    print("="*70)
    print("📦 INSTALACIÓN DE DEPENDENCIAS - BOT AVANZADO")
    print("="*70)
    
    dependencias = [
        "chromadb>=0.4.22",
        "tiktoken>=0.5.2",
    ]
    
    print("\n📋 Dependencias a instalar:")
    for dep in dependencias:
        print(f"   - {dep}")
    
    print("\n⏳ Instalando...")
    
    try:
        for dep in dependencias:
            print(f"\n📥 Instalando {dep}...")
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                dep
            ])
            print(f"✅ {dep} instalado correctamente")
        
        print("\n" + "="*70)
        print("✅ INSTALACIÓN COMPLETADA")
        print("="*70)
        
        print("""
💡 SIGUIENTE PASO:

1. Configura tu .env:
   
   # Para usar Ollama (local, gratis):
   LOCALIA=true
   
   # Para usar OpenAI (cloud):
   LOCALIA=false
   OPENAI_API_KEY=sk-tu_clave_aqui

2. Ejecuta el bot:
   python bots/bot_documentos_avanzado.py

3. O ejecuta pruebas:
   python scripts/probar_bot_avanzado.py

📚 Ver guía completa: BOT_AVANZADO.md
""")
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error durante la instalación: {e}")
        return False
    
    return True


if __name__ == "__main__":
    instalar_dependencias()
