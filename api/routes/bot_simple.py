"""Rutas API para Bot Simple"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time

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


@router.post("/query", response_model=QueryResponse, summary="Consulta general")
async def query(
    request: QueryRequest,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Realizar una consulta general al bot simple.
    
    - **pregunta**: Pregunta o consulta del usuario
    
    El bot buscará documentos relevantes y generará una respuesta usando IA.
    Si ChromaDB está disponible, usará búsqueda semántica (más eficiente).
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


@router.post("/analyze-document", response_model=QueryResponse, summary="Analizar documento específico")
async def analyze_document(
    request: AnalyzeDocumentRequest,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Analizar un documento específico por su ID de Paperless.
    
    - **documento_id**: ID del documento en Paperless
    - **pregunta** (opcional): Pregunta específica sobre el documento
    
    Si no se proporciona pregunta, genera un resumen ejecutivo.
    """
    try:
        start_time = time.time()
        
        respuesta = bot.analizar_documento(
            request.documento_id,
            request.pregunta or ""
        )
        
        tiempo_respuesta = time.time() - start_time
        
        return QueryResponse(
            respuesta=respuesta,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentosListResponse, summary="Listar todos los documentos")
async def list_documents(
    limite: int = 100,
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Obtener lista completa de documentos de Paperless.
    
    - **limite**: Número máximo de documentos a devolver (default: 100)
    
    Devuelve JSON estandarizado con:
    - id: ID del documento en Paperless
    - title: Título del documento
    - created: Fecha de creación
    - modified: Fecha de modificación
    - tags: Lista de IDs de tags
    - document_type: ID del tipo de documento
    """
    try:
        start_time = time.time()
        
        # Obtener documentos de Paperless
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
                tags=doc.get("tags", [])
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
                tags=doc.get("tags", [])
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


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(
    bot: BotDocumentos = Depends(get_bot_simple)
):
    """
    Verificar el estado del bot simple.
    
    Devuelve:
    - Estado del servicio
    - Disponibilidad de IA (Ollama)
    - Disponibilidad de ChromaDB
    - Conexión con Paperless
    - Total de documentos indexados
    """
    try:
        # Verificar estado de componentes
        ia_disponible = bot.llm is not None
        chromadb_disponible = bot.vector_store is not None
        
        # Contar documentos indexados
        total_docs = len(bot.documentos_indexados)
        
        # Intentar conectar con Paperless
        paperless_conectado = False
        try:
            docs = bot.buscar_documentos("", max_resultados=1)
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
