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


@app.get("/", tags=["General"])
async def root():
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


@app.get("/health", tags=["General"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
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
