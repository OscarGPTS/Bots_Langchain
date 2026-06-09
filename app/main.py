"""Aplicación principal FastAPI para Bots de Documentos."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.dependencies import get_bot_simple, get_bot_avanzado

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializar recursos al arrancar y limpiar al cerrar."""
    logger.info("Iniciando %s", settings.APP_NAME)

    try:
        get_bot_simple()
        logger.info("Bot Simple inicializado")
    except Exception as e:
        logger.error("Error al inicializar Bot Simple: %s", e)

    try:
        get_bot_avanzado()
        logger.info("Bot Avanzado inicializado")
    except Exception as e:
        logger.error("Error al inicializar Bot Avanzado: %s", e)

    logger.info("API lista")
    yield
    logger.info("Cerrando API")


app = FastAPI(
    title=f"{settings.APP_NAME} — API",
    description="""
    API REST para interactuar con bots inteligentes de búsqueda y análisis de documentos.

    ## 🤖 Bots Disponibles

    ### Bot Simple (`/api/v1/bot-simple`)
    - **Propósito**: Búsqueda y análisis de documentos en Paperless
    - **Tecnología**: ChromaDB + Ollama (local)

    ### Bot Avanzado (`/api/v1/bot-avanzado`)
    - **Propósito**: Análisis profundo con razonamiento
    - **Tecnología**: ChromaDB + LLM configurable (`LLM_PROVIDER`): Ollama (local),
      OpenAI o **OpenCode** (gateway). Los embeddings se mantienen locales (`LOCALIA`).

    ### 🎙️ Voz (`/api/v1/voz`)
    - **Propósito**: Consultar el RAG por voz (audio → texto → respuesta en texto y/o voz)
    - **Tecnología**: STT + TTS conmutables (`STT_PROVIDER`/`TTS_PROVIDER`): local
      (faster-whisper + Piper) u OpenAI. Requiere `VOICE_ENABLED=true`.

    ## 🔐 Autenticación

    El acceso se gestiona en el perímetro con Cloudflare Zero Trust. Las operaciones
    administrativas (p.ej. `/reindexar`) requieren además el header `X-Admin-Token`.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configurable desde settings (sin comodín + credenciales).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logging de peticiones con tiempo de proceso."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        "%s %s -> %s (%.2fs)",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api_router)


@app.get("/", tags=["General"], summary="Información de la API")
async def root():
    """Obtener información general de la API y enlaces a recursos."""
    return {
        "nombre": settings.APP_NAME,
        "version": "1.0.0",
        "estado": "activo",
        "documentacion": "/docs",
        "documentacion_alternativa": "/redoc",
        "endpoints": {
            "bot_simple": "/api/v1/bot-simple",
            "bot_avanzado": "/api/v1/bot-avanzado",
            "voz": "/api/v1/voz",
            "consultas": "/api/v1/consultas",
        },
    }


@app.get("/health", tags=["General"], summary="Health check global")
async def health_check():
    """Health check básico de la aplicación FastAPI."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.APP_NAME,
        "version": "1.0.0",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """No exponer detalles internos al cliente; registrarlos en el log."""
    logger.exception("Error no controlado en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "path": request.url.path},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=True,
        log_level="info",
    )
