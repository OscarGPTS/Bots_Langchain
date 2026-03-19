"""Aplicación principal FastAPI para Bots de Documentos"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from api.routes import bot_simple_router, bot_avanzado_router
from api.dependencies import get_bot_simple, get_bot_avanzado


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializar recursos al arrancar y limpiar al cerrar"""
    print("[INFO] Iniciando API de Bots de Documentos")
    
    try:
        get_bot_simple()
        print("[INFO] Bot Simple inicializado")
    except Exception as e:
        print(f"[ERROR] Error al inicializar Bot Simple: {e}")
    
    try:
        get_bot_avanzado()
        print("[INFO] Bot Avanzado inicializado")
    except Exception as e:
        print(f"[ERROR] Error al inicializar Bot Avanzado: {e}")
    
    print("[INFO] API lista")
    
    yield
    
    print("[INFO] Cerrando API")


# Crear aplicación FastAPI
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
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logging de peticiones"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    print(f"[REQ] {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Incluir routers
app.include_router(bot_simple_router)
app.include_router(bot_avanzado_router)


@app.get("/", tags=["General"], summary="Información de la API")
async def root():
    """
    Obtener información general de la API y enlaces a recursos.
    
    **Retorna:**
    - Nombre y versión de la API
    - Estado general
    - Enlace a documentación Swagger
    - Endpoints disponibles por bot
    
    **Endpoints disponibles:**
    
    **Bot Simple** (`/api/v1/bot-simple`):
    - `/query`: Consulta de documentos
    - `/analyze-document`: Análisis por ID
    - `/documents`: Lista de documentos
    - `/recent-documents`: Documentos recientes
    - `/health`: Estado del bot
    
    **Bot Avanzado** (`/api/v1/bot-avanzado`):
    - `/consulta-rapida`: Consulta rápida (3 chunks)
    - `/razonamiento-profundo`: Análisis profundo (hasta 20 chunks)
    - `/busqueda-semantica`: Búsqueda vectorial
    - `/stats`: Estadísticas del sistema
    - `/reindexar`: Reindexar documentos
    - `/documents`: Lista de documentos
    - `/recent-documents`: Documentos recientes
    - `/health`: Estado del bot
    """
    return {
        "nombre": "API Bots de Documentos",
        "version": "1.0.0",
        "estado": "activo",
        "documentacion": "/docs",
        "documentacion_alternativa": "/redoc",
        "endpoints": {
            "bot_simple": "/api/v1/bot-simple",
            "bot_avanzado": "/api/v1/bot-avanzado"
        },
        "tecnologias": {
            "framework": "FastAPI 0.135.1",
            "ia": ["OpenAI GPT-4o", "Ollama"],
            "vectorizacion": "ChromaDB",
            "dms": "Paperless-ngx"
        }
    }


@app.get("/health", tags=["General"], summary="Health check global")
async def health_check():
    """
    Health check básico de la API (nivel global).
    
    **Retorna:**
    - `status`: Estado del servicio (siempre "healthy" si responde)
    - `timestamp`: Timestamp Unix actual
    
    **Nota:**
    Este es un health check básico de la aplicación FastAPI.
    Para verificar componentes específicos (IA, ChromaDB, Paperless),
    usar los endpoints `/health` de cada bot:
    - `/api/v1/bot-simple/health`
    - `/api/v1/bot-avanzado/health`
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "API Bots de Documentos",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc),
            "path": request.url.path
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
