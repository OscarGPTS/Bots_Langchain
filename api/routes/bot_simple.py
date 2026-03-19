"""Rutas API para Bot Simple"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time
import os

from api.models.schemas import (
    QueryRequest, QueryResponse,
    AnalyzeDocumentRequest,
    HealthResponse, ErrorResponse,
    DocumentoPaperless, DocumentosListResponse
)
from api.dependencies import get_bot_simple
from bots.bot_documentos import BotDocumentos

router = APIRouter(
    prefix="/api/v1/bot-simple",
    tags=["Bot Simple"]
)


def _build_document_urls(doc_id: int) -> dict:
    """Construir URLs de Paperless para un documento"""
    paperless_url = os.getenv('PAPERLESS_URL', '')
    if not paperless_url:
        return {"download_url": None, "preview_url": None, "thumbnail_url": None}
    
    # Remover trailing slash si existe
    paperless_url = paperless_url.rstrip('/')
    
    return {
        "download_url": f"{paperless_url}/api/documents/{doc_id}/download/",
        "preview_url": f"{paperless_url}/api/documents/{doc_id}/preview/",
        "thumbnail_url": f"{paperless_url}/api/documents/{doc_id}/thumb/"
    }


@router.post("/query", response_model=QueryResponse, summary="Consulta general de documentos")
async def query(
    request: QueryRequest,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Realizar consulta sobre documentos de Paperless con búsqueda semántica e IA.
    
    **Funcionalidad:**
    - Busca documentos relevantes en ChromaDB usando embeddings
    - Genera respuesta inteligente usando Ollama
    - Incluye información de documentos fuente
    
    **Casos de uso:**
    - "¿Qué dice el código de ética sobre integridad?"
    - "Busca contratos de 2026"
    - "Resume la política de vacaciones"
    
    **Limitaciones:**
    - Solo busca en documentos de Paperless
    - No consulta información de RH/empleados
    - Usa modelo local (Ollama)
    """
    try:
        start_time = time.time()
        respuesta = bot.procesar(request.pregunta)
        tiempo_respuesta = time.time() - start_time
        
        return QueryResponse(
            respuesta=respuesta,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-document", response_model=QueryResponse, summary="Analizar documento específico por ID")
async def analyze_document(
    request: AnalyzeDocumentRequest,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Analizar un documento específico de Paperless por su ID.
    
    **Funcionalidad:**
    - Extrae contenido completo del documento (OCR)
    - Responde preguntas específicas sobre el documento
    - Si no se proporciona pregunta, genera resumen ejecutivo
    
    **Parámetros:**
    - `documento_id`: ID del documento en Paperless (requerido)
    - `pregunta`: Pregunta específica (opcional)
    
    **Ejemplos:**
    - Resumen: `{"documento_id": 1}`
    - Análisis: `{"documento_id": 1, "pregunta": "¿Cuáles son las condiciones de pago?"}`
    """
    try:
        start_time = time.time()
        respuesta = bot.analizar_documento(request.documento_id, request.pregunta or "")
        tiempo_respuesta = time.time() - start_time
        
        return QueryResponse(
            respuesta=respuesta,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentosListResponse, summary="Listar documentos de Paperless")
async def list_documents(
    limite: int = 100,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Obtener lista de documentos de Paperless (ordenados por más recientes).
    
    **Parámetros:**
    - `limite`: Número máximo de documentos a devolver (default: 100, max: 100)
    
    **Retorna:**
    - Lista de documentos con metadata (ID, título, fecha, tags, etc.)
    - Total de documentos
    - Tiempo de respuesta
    
    **Formato:**
    - JSON estandarizado compatible con Paperless API
    - Incluye: id, title, created, modified, tags, document_type, correspondent
    """
    try:
        start_time = time.time()
        documentos_raw = bot.buscar_documentos("", max_resultados=limite)
        
        documentos = [
            DocumentoPaperless(
                id=doc.get("id"),
                title=doc.get("title", "Sin título"),
                created=doc.get("created", ""),
                modified=doc.get("modified"),
                archive_serial_number=doc.get("archive_serial_number"),
                correspondent=doc.get("correspondent"),
                document_type=doc.get("document_type"),
                tags=doc.get("tags", []),
                **_build_document_urls(doc.get("id"))
            )
            for doc in documentos_raw
        ]
        
        tiempo_respuesta = time.time() - start_time
        
        return DocumentosListResponse(
            documentos=documentos,
            total=len(documentos),
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-documents", response_model=DocumentosListResponse, summary="Listar documentos recientes")
async def recent_documents(
    limite: int = 10,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Obtener lista de documentos recientes de Paperless (ordenados por fecha).
    
    - **limite**: Número de documentos a devolver (default: 10)
    
    Devuelve JSON estandarizado con los últimos documentos:
    - id: ID del documento
    - title: Título
    - created: Fecha de creación
    - modified: Fecha de modificación
    - tags: IDs de tags
    """
    try:
        start_time = time.time()
        
        # Obtener documentos recientes
        documentos_raw = bot.buscar_documentos("", max_resultados=limite)
        
        # Convertir a formato estandarizado
        documentos = [
            DocumentoPaperless(
                id=doc.get("id"),
                title=doc.get("title", "Sin título"),
                created=doc.get("created", ""),
                modified=doc.get("modified"),
                archive_serial_number=doc.get("archive_serial_number"),
                correspondent=doc.get("correspondent"),
                document_type=doc.get("document_type"),
                tags=doc.get("tags", []),
                **_build_document_urls(doc.get("id"))
            )
            for doc in documentos_raw
        ]
        
        tiempo_respuesta = time.time() - start_time
        
        return DocumentosListResponse(
            documentos=documentos,
            total=len(documentos),
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse, summary="Estado del bot simple")
async def health(
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Verificar estado del bot simple y sus componentes.
    
    **Componentes verificados:**
    - IA (Ollama): disponibilidad del modelo
    - ChromaDB: estado de la base de vectores
    - Paperless: conexión con servidor
    - Documentos: total indexados
    
    **Estados posibles:**
    - `healthy`: Todos los componentes funcionando
    - `degraded`: Algunos componentes con problemas
    - `unhealthy`: Servicio no disponible
    """
    try:
        ia_disponible = bot.llm is not None
        chromadb_disponible = bot.vector_store is not None
        total_docs = len(bot.documentos_indexados)
        
        paperless_conectado = False
        try:
            bot.buscar_documentos("", max_resultados=1)
            paperless_conectado = True
        except:
            pass
        
        return HealthResponse(
            status="healthy" if all([ia_disponible, paperless_conectado]) else "degraded",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            ia_disponible=ia_disponible,
            chromadb_disponible=chromadb_disponible,
            paperless_conectado=paperless_conectado,
            total_documentos=total_docs
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
