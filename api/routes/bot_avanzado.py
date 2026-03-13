"""Rutas API para Bot Avanzado"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import time
import os

from api.models.schemas import (
    QueryAvanzadaRequest, QueryAvanzadaResponse,
    RazonamientoRequest,
    BusquedaSemanticaRequest, BusquedaSemanticaResponse, DocumentoInfo,
    StatsResponse, DocumentoIndexado,
    HealthResponse, ReindexarResponse,
    DocumentoPaperless, DocumentosListResponse
)
from api.dependencies import get_bot_avanzado
from bots.bot_documentos_avanzado import BotDocumentosAvanzado

router = APIRouter(
    prefix="/api/v1/bot-avanzado",
    tags=["Bot Avanzado"]
)


@router.post("/consulta-rapida", response_model=QueryAvanzadaResponse, summary="Consulta rápida")
async def consulta_rapida(
    request: QueryAvanzadaRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Consulta rápida con el bot avanzado.
    
    - **pregunta**: Consulta del usuario
    - **filtros** (opcional): Filtros de metadata (ej: {"tags": "contrato"})
    
    Usa:
    - Solo 3 chunks más relevantes
    - Modelo rápido (gpt-4o-mini o Ollama)
    - Ideal para consultas simples y directas
    """
    try:
        start_time = time.time()
        
        respuesta, stats = bot.consulta_rapida(
            request.pregunta,
            request.filtros
        )
        
        tiempo_respuesta = time.time() - start_time
        
        return QueryAvanzadaResponse(
            respuesta=respuesta,
            estadisticas=stats,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/razonamiento-profundo", response_model=QueryAvanzadaResponse, summary="Razonamiento profundo")
async def razonamiento_profundo(
    request: RazonamientoRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Análisis profundo con razonamiento complejo.
    
    - **pregunta**: Pregunta compleja que requiere análisis
    - **filtros** (opcional): Filtros de metadata
    - **k**: Número de chunks a analizar (1-20, default: 10)
    
    Usa:
    - Hasta 20 chunks para análisis profundo
    - Modelo con razonamiento (gpt-4o o Ollama)
    - Ideal para análisis complejos, comparaciones, tendencias
    """
    try:
        start_time = time.time()
        
        respuesta, stats = bot.razonamiento_profundo(
            request.pregunta,
            request.filtros,
            request.k
        )
        
        tiempo_respuesta = time.time() - start_time
        
        return QueryAvanzadaResponse(
            respuesta=respuesta,
            estadisticas=stats,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/busqueda-semantica", response_model=BusquedaSemanticaResponse, summary="Búsqueda semántica")
async def busqueda_semantica(
    request: BusquedaSemanticaRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Búsqueda semántica en la base de vectores.
    
    - **query**: Texto de búsqueda
    - **k**: Número de resultados (1-20, default: 5)
    - **filtros** (opcional): Filtros de metadata
    
    Devuelve los chunks más similares semánticamente sin generar respuesta.
    Útil para exploración y verificación.
    """
    try:
        start_time = time.time()
        
        resultados = bot.buscar_semantica(
            request.query,
            request.k,
            request.filtros
        )
        
        tiempo_respuesta = time.time() - start_time
        
        # Convertir documentos a formato response
        docs_info = []
        for doc in resultados:
            docs_info.append(DocumentoInfo(
                doc_id=doc.metadata.get('doc_id', ''),
                title=doc.metadata.get('title', ''),
                chunk_index=doc.metadata.get('chunk_index', 0),
                total_chunks=doc.metadata.get('total_chunks', 0),
                created=doc.metadata.get('created', '')[:10],
                preview=doc.page_content[:200]
            ))
        
        return BusquedaSemanticaResponse(
            resultados=docs_info,
            total=len(docs_info),
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse, summary="Estadísticas")
async def get_stats(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Obtener estadísticas del bot avanzado.
    
    Devuelve:
    - Total de documentos indexados
    - Total de vectores en ChromaDB
    - Modo actual (local/cloud)
    - Modelos configurados
    - Lista de documentos indexados
    """
    try:
        # Obtener modo
        modo = "local (Ollama)" if os.getenv('LOCALIA', 'true').lower() == 'true' else "cloud (OpenAI)"
        
        # Contar vectores
        total_vectores = 0
        if bot.vector_store:
            try:
                collection = bot.vector_store._collection
                total_vectores = collection.count()
            except:
                pass
        
        # Obtener documentos indexados
        docs_indexados = []
        # TODO: Implementar lista detallada de documentos desde ChromaDB
        
        return StatsResponse(
            total_documentos=len(bot.documentos_indexados),
            total_vectores=total_vectores,
            modo=modo,
            modelo_rapido=os.getenv('OPENAI_MODEL_RAPIDO', 'gpt-4o-mini') if modo == "cloud" else os.getenv('OLLAMA_MODEL', 'phi4-mini'),
            modelo_razonamiento=os.getenv('OPENAI_MODEL_RAZONAMIENTO', 'gpt-4o') if modo == "cloud" else os.getenv('OLLAMA_MODEL', 'phi4-mini'),
            documentos_indexados=docs_indexados
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindexar", response_model=ReindexarResponse, summary="Forzar reindexación")
async def reindexar(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Forzar reindexación de todos los documentos.
    
    **ADVERTENCIA**: Esta operación puede tardar varios minutos.
    
    - Descarga todos los documentos de Paperless
    - Re-vectoriza todos los chunks
    - Actualiza ChromaDB
    
    Útil cuando:
    - Se actualizan documentos en Paperless
    - Se cambia el modelo de embeddings
    - Se corrompe la base de datos de vectores
    """
    try:
        start_time = time.time()
        
        # Contar documentos antes
        docs_antes = len(bot.documentos_indexados)
        
        # Limpiar documentos indexados para forzar reindexación
        bot.documentos_indexados.clear()
        
        # Recargar documentos
        bot._cargar_documentos_paperless()
        
        # Contar documentos después
        docs_despues = len(bot.documentos_indexados)
        
        tiempo_total = time.time() - start_time
        
        return ReindexarResponse(
            mensaje="Reindexación completada",
            documentos_nuevos=docs_despues - docs_antes,
            documentos_actualizados=docs_despues,
            tiempo_total=round(tiempo_total, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentosListResponse, summary="Listar todos los documentos")
async def list_documents(
    limite: int = 100,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
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
        import requests
        start_time = time.time()
        
        # Obtener documentos directamente de Paperless
        PAPERLESS_URL = os.getenv('PAPERLESS_URL')
        PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
        
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            raise HTTPException(status_code=503, detail="Paperless no configurado")
        
        headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
        params = {
            'page_size': limite,
            'ordering': '-created'
        }
        
        response = requests.get(
            f"{PAPERLESS_URL}/api/documents/",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        documentos_raw = response.json().get('results', [])
        
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
    
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error conectando con Paperless: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-documents", response_model=DocumentosListResponse, summary="Listar documentos recientes")
async def recent_documents(
    limite: int = 10,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
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
        import requests
        start_time = time.time()
        
        # Obtener documentos directamente de Paperless
        PAPERLESS_URL = os.getenv('PAPERLESS_URL')
        PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
        
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            raise HTTPException(status_code=503, detail="Paperless no configurado")
        
        headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
        params = {
            'page_size': limite,
            'ordering': '-created'
        }
        
        response = requests.get(
            f"{PAPERLESS_URL}/api/documents/",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        documentos_raw = response.json().get('results', [])
        
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
    
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error conectando con Paperless: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Verificar el estado del bot avanzado.
    
    Devuelve:
    - Estado del servicio
    - Disponibilidad de modelos de IA
    - Disponibilidad de ChromaDB
    - Conexión con Paperless
    - Total de documentos indexados
    """
    try:
        # Verificar componentes
        ia_disponible = (bot.llm_rapido is not None) and (bot.llm_razonamiento is not None)
        chromadb_disponible = bot.vector_store is not None
        
        # Contar documentos
        total_docs = len(bot.documentos_indexados)
        
        # Verificar Paperless (intentar buscar)
        paperless_conectado = False
        try:
            import requests
            from dotenv import load_dotenv
            load_dotenv()
            
            PAPERLESS_URL = os.getenv('PAPERLESS_URL')
            PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
            
            if PAPERLESS_URL and PAPERLESS_TOKEN:
                headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
                response = requests.get(
                    f"{PAPERLESS_URL}/api/documents/",
                    headers=headers,
                    params={'page_size': 1},
                    timeout=5
                )
                paperless_conectado = response.status_code == 200
        except:
            pass
        
        return HealthResponse(
            status="healthy" if all([ia_disponible, chromadb_disponible, paperless_conectado]) else "degraded",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            ia_disponible=ia_disponible,
            chromadb_disponible=chromadb_disponible,
            paperless_conectado=paperless_conectado,
            total_documentos=total_docs
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
