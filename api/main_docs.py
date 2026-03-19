"""Aplicación FastAPI simplificada para ver documentación"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from api.routes import bot_simple_router, bot_avanzado_router

# Crear aplicación FastAPI sin lifespan
app = FastAPI(
    title="API Bots de Documentos",
    description="""
    API REST para interactuar con bots inteligentes de búsqueda y análisis de documentos.
    
    ## 🤖 Bots Disponibles
    
    ### Bot Simple (`/api/v1/bot-simple`)
    - **Propósito**: Búsqueda y análisis de documentos en Paperless
    - **Tecnología**: ChromaDB + Ollama (local)
    - **Velocidad**: Rápida
    - **Uso**: Consultas sencillas sobre documentos
    - **Endpoints**: `/query`, `/analyze-document`, `/documents`, `/recent-documents`
    
    ### Bot Avanzado (`/api/v1/bot-avanzado`)
    - **Propósito**: Análisis profundo con razonamiento
    - **Tecnología**: OpenAI GPT-4o / GPT-4o-mini o Ollama
    - **Modos**: Consulta Rápida (3 chunks) y Razonamiento Profundo (hasta 20 chunks)
    - **Características**: Context caching, monitoreo de tokens/costos
    - **Endpoints**: `/consulta-rapida`, `/razonamiento-profundo`, `/busqueda-semantica`, `/stats`, `/reindexar`
    
    ## 🔧 Características
    
    * **Búsqueda Semántica**: Vectorización con ChromaDB
    * **IA Dual**: Soporte para OpenAI (cloud) y Ollama (local)
    * **Persistencia**: ChromaDB almacena vectores en disco
    * **Monitoreo**: Estadísticas de uso y costos (OpenAI)
    * **Health Checks**: Estado de componentes en tiempo real
    
    ## 🔐 Autenticación
    
    Actualmente sin autenticación. Para producción, configurar JWT, API Keys o Cloudflare Zero Trust.
    
    ## 📚 Documentación
    
    - **Swagger UI**: `/docs` (esta página)
    - **ReDoc**: `/redoc` (formato alternativo)
    - **Health Check**: `/health`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(bot_simple_router)
app.include_router(bot_avanzado_router)

@app.get("/", tags=["General"], summary="Información de la API")
async def root():
    """Obtener información general de la API"""
    return {
        "nombre": "API Bots de Documentos (Modo Documentación)",
        "version": "1.0.0",
        "estado": "solo documentación",
        "mensaje": "Este servidor está corriendo en modo de documentación solamente. Los endpoints funcionales requieren inicializar los bots.",
        "documentacion": "/docs",
        "documentacion_alternativa": "/redoc",
        "endpoints": {
            "bot_simple": "/api/v1/bot-simple",
            "bot_avanzado": "/api/v1/bot-avanzado"
        }
    }

@app.get("/health", tags=["General"], summary="Health check")
async def health_check():
    """Health check básico"""
    return {
        "status": "healthy",
        "mode": "documentation_only",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    print("""
╔════════════════════════════════════════════════════════════════╗
║      API Bots - Modo Documentación (sin inicializar bots)     ║
╚════════════════════════════════════════════════════════════════╝

📚 Ver documentación en: http://localhost:8003/docs
📖 ReDoc alternativo: http://localhost:8003/redoc

Presiona Ctrl+C para detener
""")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8003,
        log_level="info"
    )
