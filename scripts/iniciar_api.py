"""Script para iniciar la API de Bots de Documentos"""
import uvicorn
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         API de Bots de Documentos - Servidor FastAPI         ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    📚 Documentación interactiva: http://localhost:8000/docs
    📖 Documentación alternativa: http://localhost:8000/redoc
    🏥 Health check: http://localhost:8000/health
    
    Presiona Ctrl+C para detener el servidor
    """)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo (desactivar en producción)
        log_level="info",
        access_log=True
    )
