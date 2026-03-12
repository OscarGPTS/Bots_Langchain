"""Script rápido para probar que la API funciona"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("PROBANDO IMPORTACIONES DE LA API")
print("="*70)
print()

try:
    print("1. Importando FastAPI...")
    from fastapi import FastAPI
    print("   OK - FastAPI importado")
    
    print("\n2. Importando schemas...")
    from api.models.schemas import QueryRequest, QueryResponse
    print("   OK - Schemas importados")
    
    print("\n3. Importando rutas...")
    from api.routes import bot_simple_router, bot_avanzado_router
    print("   OK - Rutas importadas")
    
    print("\n4. Importando dependencias...")
    from api.dependencies import get_bot_simple, get_bot_avanzado
    print("   OK - Dependencias importadas")
    
    print("\n5. Importando aplicación principal...")
    from api.main import app
    print("   OK - Aplicación principal importada")
    
    print("\n" + "="*70)
    print("TODAS LAS IMPORTACIONES EXITOSAS")
    print("="*70)
    print()
    print("Para iniciar la API ejecuta:")
    print("  python scripts/iniciar_api.py")
    print()
    print("O directamente:")
    print("  uvicorn api.main:app --reload")
    print()
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
