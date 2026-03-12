"""Ejemplo de cliente para consumir la API de Bots"""
import requests
import json

# URL base de la API
BASE_URL = "http://localhost:8000"


def probar_bot_simple():
    """Probar endpoints del bot simple"""
    print("\n" + "="*70)
    print("PROBANDO BOT SIMPLE")
    print("="*70)
    
    # 1. Health check
    print("\n1. Health check...")
    response = requests.get(f"{BASE_URL}/api/v1/bot-simple/health")
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Estado: {data['status']}")
        print(f"   IA disponible: {data['ia_disponible']}")
        print(f"   ChromaDB: {data['chromadb_disponible']}")
    
    # 2. Consulta simple
    print("\n2. Consulta simple...")
    response = requests.post(
        f"{BASE_URL}/api/v1/bot-simple/query",
        json={"pregunta": "¿Qué dice el código de ética sobre integridad?"}
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Tiempo: {data['tiempo_respuesta']}s")
        print(f"   Respuesta: {data['respuesta'][:200]}...")
    
    # 3. Documentos recientes
    print("\n3. Documentos recientes...")
    response = requests.get(f"{BASE_URL}/api/v1/bot-simple/recent-documents")
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Tiempo: {data['tiempo_respuesta']}s")
        print(f"   Documentos: {len(data['respuesta'].split('📄'))}")


def probar_bot_avanzado():
    """Probar endpoints del bot avanzado"""
    print("\n" + "="*70)
    print("PROBANDO BOT AVANZADO")
    print("="*70)
    
    # 1. Health check
    print("\n1. Health check...")
    response = requests.get(f"{BASE_URL}/api/v1/bot-avanzado/health")
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Estado: {data['status']}")
        print(f"   Documentos indexados: {data['total_documentos']}")
    
    # 2. Consulta rápida
    print("\n2. Consulta rápida...")
    response = requests.post(
        f"{BASE_URL}/api/v1/bot-avanzado/consulta-rapida",
        json={
            "pregunta": "¿Cuál es el horario de trabajo?",
            "filtros": None
        }
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Tiempo: {data['tiempo_respuesta']}s")
        if data['estadisticas']:
            print(f"   Tokens: {data['estadisticas'].get('tokens_total', 'N/A')}")
        print(f"   Respuesta: {data['respuesta'][:200]}...")
    
    # 3. Búsqueda semántica
    print("\n3. Búsqueda semántica...")
    response = requests.post(
        f"{BASE_URL}/api/v1/bot-avanzado/busqueda-semantica",
        json={
            "query": "políticas de seguridad",
            "k": 3
        }
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Tiempo: {data['tiempo_respuesta']}s")
        print(f"   Resultados: {data['total']}")
        if data['resultados']:
            print(f"   Primer resultado: {data['resultados'][0]['title']}")
    
    # 4. Estadísticas
    print("\n4. Estadísticas...")
    response = requests.get(f"{BASE_URL}/api/v1/bot-avanzado/stats")
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Documentos: {data['total_documentos']}")
        print(f"   Vectores: {data['total_vectores']}")
        print(f"   Modo: {data['modo']}")
        print(f"   Modelo rápido: {data['modelo_rapido']}")


def main():
    """Ejecutar todas las pruebas"""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║         Cliente de Prueba - API de Bots de Documentos        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    # Verificar que la API esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if not response.ok:
            print("\n❌ Error: La API no está respondiendo correctamente")
            print("   Inicia la API con: python scripts/iniciar_api.py")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar a la API")
        print("   Asegúrate de que la API esté corriendo en http://localhost:8000")
        print("   Inicia la API con: python scripts/iniciar_api.py")
        return
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return
    
    print("\n✅ API está corriendo")
    
    # Ejecutar pruebas
    try:
        probar_bot_simple()
        probar_bot_avanzado()
        
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*70)
        print("\n💡 Abre http://localhost:8000/docs para explorar más endpoints")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
