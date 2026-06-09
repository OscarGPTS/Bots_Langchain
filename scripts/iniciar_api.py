"""Script para iniciar la API de Bots de Documentos"""
import uvicorn
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

if __name__ == "__main__":
    port = settings.API_PORT

    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         API de Bots de Documentos - Servidor FastAPI         ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    📚 Documentación interactiva: http://localhost:{port}/docs
    📖 Documentación alternativa: http://localhost:{port}/redoc
    🏥 Health check: http://localhost:{port}/health
    
    Presiona Ctrl+C para detener el servidor
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Auto-reload en desarrollo (desactivar en producción)
        log_level="info",
        access_log=True
    )
