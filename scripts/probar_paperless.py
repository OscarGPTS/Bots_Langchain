"""
Script para Probar Conexión con Paperless
==========================================
Verifica que tu URL y Token funcionen correctamente.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def probar_paperless():
    """Prueba la conexión con Paperless-ngx"""
    
    print("=" * 70)
    print("🔍 PROBANDO CONEXIÓN CON PAPERLESS")
    print("=" * 70)
    print()
    
    # Verificar configuración
    url = os.getenv('PAPERLESS_URL')
    token = os.getenv('PAPERLESS_TOKEN')
    
    if not url:
        print("❌ Error: No has configurado PAPERLESS_URL")
        print()
        print("📝 Edita el archivo .env:")
        print('   PAPERLESS_URL=https://tu-paperless.com')
        print()
        return
    
    if not token:
        print("❌ Error: No has configurado PAPERLESS_TOKEN")
        print()
        print("🔑 Para obtener un token, ejecuta:")
        print("   python scripts/generar_token_paperless.py")
        print()
        print("📝 Luego edita el archivo .env:")
        print('   PAPERLESS_TOKEN=tu_token_aqui')
        print()
        return
    
    print(f"📡 URL: {url}")
    print(f"🔑 Token: {token[:20]}...")
    print()
    
    # Preparar headers
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Probar endpoints
    print("🧪 Probando endpoints...")
    print()
    
    # 1. Probar conexión básica
    try:
        response = requests.get(
            f"{url}/api/documents/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Conexión exitosa")
            data = response.json()
            
            total = data.get('count', 0)
            documentos = data.get('results', [])
            
            print()
            print("=" * 70)
            print("📊 ESTADÍSTICAS DE PAPERLESS")
            print("=" * 70)
            print(f"\n📄 Total de documentos: {total}")
            
            if documentos:
                print(f"📄 Documentos en esta página: {len(documentos)}")
                print()
                print("📋 Primeros 3 documentos:")
                for i, doc in enumerate(documentos[:3], 1):
                    print(f"\n{i}. {doc.get('title', 'Sin título')}")
                    print(f"   ID: {doc.get('id')}")
                    print(f"   Creado: {doc.get('created', 'N/A')[:10]}")
                    if doc.get('correspondent'):
                        print(f"   De: {doc.get('correspondent_name', 'N/A')}")
            
            # Probar búsqueda
            print()
            print("=" * 70)
            print("🔍 PROBANDO BÚSQUEDA")
            print("=" * 70)
            
            search_response = requests.get(
                f"{url}/api/documents/?query=*",
                headers=headers,
                timeout=10
            )
            
            if search_response.status_code == 200:
                print("✅ Búsqueda funciona correctamente")
            
            # Obtener etiquetas
            tags_response = requests.get(
                f"{url}/api/tags/",
                headers=headers,
                timeout=10
            )
            
            if tags_response.status_code == 200:
                tags_data = tags_response.json()
                tags = tags_data.get('results', [])
                print(f"🏷️  Etiquetas disponibles: {len(tags)}")
                
                if tags:
                    print()
                    print("Etiquetas:")
                    for tag in tags[:5]:
                        count = tag.get('document_count', 0)
                        print(f"   • {tag.get('name')}: {count} documentos")
            
            # Obtener tipos de documento
            types_response = requests.get(
                f"{url}/api/document_types/",
                headers=headers,
                timeout=10
            )
            
            if types_response.status_code == 200:
                types_data = types_response.json()
                types = types_data.get('results', [])
                print(f"\n📑 Tipos de documento: {len(types)}")
                
                if types:
                    print()
                    print("Tipos:")
                    for dtype in types[:5]:
                        count = dtype.get('document_count', 0)
                        print(f"   • {dtype.get('name')}: {count} documentos")
            
            print()
            print("=" * 70)
            print("✅ PAPERLESS ESTÁ LISTO PARA USAR")
            print("=" * 70)
            print()
            print("🚀 Siguiente paso:")
            print("   python bot_paperless_sin_ia.py  # Búsqueda rápida")
            print("   python bot_paperless_con_ia.py  # Con inteligencia artificial")
            print()
            
        elif response.status_code == 401:
            print("❌ Error 401: Token inválido o expirado")
            print()
            print("💡 Soluciones:")
            print("   1. Verifica que el token sea correcto")
            print("   2. Genera un nuevo token:")
            print("      python generar_token_paperless.py")
            print()
            
        elif response.status_code == 403:
            print("❌ Error 403: Sin permisos")
            print("💡 Tu token no tiene permisos suficientes")
            print()
            
        elif response.status_code == 404:
            print("❌ Error 404: URL incorrecta")
            print(f"💡 Verifica la URL: {url}")
            print()
            
        else:
            print(f"❌ Error {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            print()
    
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - El servidor no respondió")
        print("💡 Verifica que Paperless esté corriendo")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar")
        print(f"💡 Verifica la URL: {url}")
        print("💡 Verifica tu conexión a red")
        print()
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print()

if __name__ == "__main__":
    probar_paperless()
