"""Aplicación principal FastAPI para Bots de Documentos"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from api.routes import bot_simple_router, bot_avanzado_router
from api.dependencies import get_bot_simple, get_bot_avanzado


# Lifespan para inicializar bots al arrancar
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializar recursos al arrancar y limpiar al cerrar"""
    # Startup
    print("\n" + "="*70)
    print("🚀 Iniciando API de Bots de Documentos")
    print("="*70)
    
    # Pre-cargar bots (opcional, para startup más rápido)
    print("\n📦 Pre-cargando bots...")
    try:
        get_bot_simple()
        print("✅ Bot Simple inicializado")
    except Exception as e:
        print(f"⚠️ Error al inicializar Bot Simple: {e}")
    
    try:
        get_bot_avanzado()
        print("✅ Bot Avanzado inicializado")
    except Exception as e:
        print(f"⚠️ Error al inicializar Bot Avanzado: {e}")
    
    print("\n" + "="*70)
    print("✅ API lista para recibir peticiones")
    print("📚 Documentación: http://localhost:8000/docs")
    print("="*70 + "\n")
    
    yield
    
    # Shutdown
    print("\n👋 Cerrando API...")


# Crear aplicación FastAPI
app = FastAPI(
    title="API Bots de Documentos",
    description="""
    API REST para interactuar con bots inteligentes de búsqueda y análisis de documentos.
    
    ## Características
    
    * **Bot Simple**: Búsqueda rápida con ChromaDB y Ollama local
    * **Bot Avanzado**: Análisis profundo con OpenAI o Ollama, context caching
    * **Búsqueda Semántica**: Vectorización con ChromaDB
    * **Documentación automática**: Swagger UI y ReDoc
    
    ## Autenticación
    
    Actualmente sin autenticación. Para producción, agregar JWT o API Keys.
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

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logging de todas las peticiones"""
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo
    process_time = time.time() - start_time
    
    # Log
    print(f"📥 {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    
    # Agregar header con tiempo de procesamiento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Incluir routers
app.include_router(bot_simple_router)
app.include_router(bot_avanzado_router)


# Ruta raíz
@app.get("/", tags=["General"])
async def root():
    """Información básica de la API"""
    return {
        "nombre": "API Bots de Documentos",
        "version": "1.0.0",
        "estado": "activo",
        "documentacion": "/docs",
        "endpoints": {
            "bot_simple": "/api/v1/bot-simple",
            "bot_avanzado": "/api/v1/bot-avanzado"
        }
    }


# Health check global
@app.get("/health", tags=["General"])
async def health_check():
    """Health check global de la API"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "bot_simple": "/api/v1/bot-simple/health",
            "bot_avanzado": "/api/v1/bot-avanzado/health"
        }
    }


# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
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
    
    # Ejecutar servidor
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
