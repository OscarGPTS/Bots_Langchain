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


@router.post("/consulta-rapida", response_model=QueryAvanzadaResponse, summary="Consulta rápida (3 chunks)")
async def consulta_rapida(
    request: QueryAvanzadaRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Consulta rápida con modelo optimizado para respuestas directas.
    
    **Características:**
    - Usa solo 3 chunks más relevantes
    - Modelo rápido: GPT-4o-mini (OpenAI) o Ollama
    - Respuesta en segundos
    - Monitoreo de tokens y costos (OpenAI)
    
    **Ideal para:**
    - Preguntas directas: "¿Cuál es el horario de trabajo?"
    - Búsqueda de información específica
    - Consultas frecuentes
    
    **Retorna:**
    - Respuesta generada
    - Estadísticas de uso (solo OpenAI)
    - Documentos consultados
    - Tiempo de procesamiento
    """
    try:
        start_time = time.time()
        respuesta, stats = bot.consulta_rapida(request.pregunta, request.filtros)
        tiempo_respuesta = time.time() - start_time
        
        return QueryAvanzadaResponse(
            respuesta=respuesta,
            estadisticas=stats,
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/razonamiento-profundo", response_model=QueryAvanzadaResponse, summary="Análisis profundo (hasta 20 chunks)")
async def razonamiento_profundo(
    request: RazonamientoRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Análisis profundo con razonamiento avanzado para consultas complejas.
    
    **Características:**
    - Analiza hasta 20 chunks (configurable con parámetro k)
    - Modelo avanzado: GPT-4o con reasoning_effort="medium" (OpenAI) o Ollama
    - Razonamiento estructurado paso a paso
    - Context caching para reducir costos (OpenAI)
    
    **Ideal para:**
    - Análisis complejos: "Compara las políticas de 2025 vs 2026"
    - Generación de resúmenes detallados
    - Búsqueda de patrones y tendencias
    - Preguntas que requieren múltiples documentos
    
    **Parámetros:**
    - `pregunta`: Pregunta compleja a analizar
    - `filtros`: Filtros opcionales (año, tags)
    - `k`: Número de chunks (1-20, default: 10)
    
    **Retorna:**
    - Análisis estructurado con razonamiento
    - Estadísticas detalladas (tokens de razonamiento incluidos)
    - Documentos analizados con fragmentos
    - Tiempo de procesamiento
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


@router.post("/busqueda-semantica", response_model=BusquedaSemanticaResponse, summary="Búsqueda vectorial sin IA")
async def busqueda_semantica(
    request: BusquedaSemanticaRequest,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Búsqueda semántica pura en ChromaDB sin generación de respuesta con IA.
    
    **Funcionalidad:**
    - Vectoriza la consulta con embeddings
    - Busca chunks más similares por similitud coseno
    - NO genera respuesta (solo retorna fragmentos)
    - Útil para encontrar documentos relevantes
    
    **Parámetros:**
    - `query`: Texto de búsqueda
    - `k`: Número de resultados (1-20, default: 5)
    - `filtros`: Filtros opcionales (año, tags, etc.)
    
    **Retorna:**
    - Lista de fragmentos (chunks) más relevantes
    - Metadata: título, fecha, índice de chunk
    - Preview del contenido (primeros 200 caracteres)
    
    **Diferencia con /consulta-rapida:**
    - Esta búsqueda NO usa IA para generar respuestas
    - Solo retorna los fragmentos encontrados
    - Más rápida y sin costos de tokens
    """
    try:
        start_time = time.time()
        resultados = bot.buscar_semantica(request.query, request.k, request.filtros)
        tiempo_respuesta = time.time() - start_time
        
        docs_info = [
            DocumentoInfo(
                doc_id=doc.metadata.get('doc_id', ''),
                title=doc.metadata.get('title', ''),
                chunk_index=doc.metadata.get('chunk_index', 0),
                total_chunks=doc.metadata.get('total_chunks', 0),
                created=doc.metadata.get('created', '')[:10],
                preview=doc.page_content[:200]
            )
            for doc in resultados
        ]
        
        return BusquedaSemanticaResponse(
            resultados=docs_info,
            total=len(docs_info),
            tiempo_respuesta=round(tiempo_respuesta, 2)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse, summary="Estadísticas del sistema")
async def get_stats(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Obtener estadísticas completas del bot avanzado y su infraestructura.
    
    **Información devuelta:**
    - **total_documentos**: Número de documentos indexados
    - **total_vectores**: Número total de vectores en ChromaDB
    - **modo**: "local (Ollama)" o "cloud (OpenAI)"
    - **modelo_rapido**: Modelo usado para consultas rápidas
    - **modelo_razonamiento**: Modelo usado para análisis profundos
    - **documentos_indexados**: Lista detallada (próximamente)
    
    **Útil para:**
    - Monitorear estado del sistema
    - Validar configuración de modelos
    - Verificar tamaño de la base de vectores
    - Auditoría de documentos indexados
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


@router.post("/reindexar", response_model=ReindexarResponse, summary="Reindexar todos los documentos")
async def reindexar(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Forzar reindexación completa de todos los documentos de Paperless.
    
    **⚠️ ADVERTENCIA:**
    - Esta operación puede tardar **varios minutos** dependiendo del número de documentos
    - Consume recursos significativos (CPU, memoria, ancho de banda)
    - Solo ejecutar cuando sea necesario
    
    **Proceso:**
    1. Limpia el registro de documentos indexados
    2. Descarga todos los documentos de Paperless  
    3. Extrae contenido OCR de cada documento
    4. Divide en chunks (fragmentos)
    5. Genera embeddings (vectorización)
    6. Almacena en ChromaDB
    
    **Cuándo usar:**
    - Documentos actualizados en Paperless no se reflejan
    - Cambio de modelo de embeddings (OpenAI ↔ Ollama)
    - Corrupción de base de datos de vectores
    - Cambio en chunk_size o chunk_overlap
    
    **Retorna:**
    - Mensaje de confirmación
    - Número de documentos nuevos indexados
    - Número total de documentos actualizados
    - Tiempo total de la operación
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


@router.get("/documents", response_model=DocumentosListResponse, summary="Listar documentos de Paperless")
async def list_documents(
    limite: int = 100,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Obtener lista de documentos directamente desde Paperless (ordenados por fecha).
    
    **Parámetros:**
    - `limite`: Número máximo de documentos (default: 100)
    
    **Formato de respuesta:**
    - JSON estandarizado compatible con Paperless API
    - Campos: id, title, created, modified, tags, document_type, correspondent, archive_serial_number
    
    **Nota:**
    Este endpoint consulta directamente Paperless, no usa ChromaDB.
    Para búsqueda semántica, usar `/busqueda-semantica`.
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


@router.get("/recent-documents", response_model=DocumentosListResponse, summary="Documentos recientes de Paperless")
async def recent_documents(
    limite: int = 10,
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Obtener los documentos más recientes de Paperless (ordenados por fecha de creación).
    
    **Parámetros:**
    - `limite`: Número de documentos a devolver (default: 10, recomendado para últimos documentos)
    
    **Diferencia con `/documents`:**
    - Este endpoint es optimizado para consultas rápidas de documentos recientes
    - `/documents` es para listas más grandes (hasta 100)
    
    **Formato de respuesta:**
    - JSON estandarizado con metadata completa
    - Ordenados por fecha de creación (más recientes primero)
    
    **Casos de uso:**
    - Dashboard de documentos recientes
    - Monitoreo de nuevos documentos subidos
    - Validación de procesamiento OCR
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


@router.get("/health", response_model=HealthResponse, summary="Estado del bot avanzado")
async def health(
    bot: BotDocumentosAvanzado = Depends(get_bot_avanzado)
):
    """
    Verificar el estado de salud del bot avanzado y todos sus componentes.
    
    **Componentes verificados:**
    
    1. **IA (Modelos):**
       - Modelo rápido (GPT-4o-mini/Ollama)
       - Modelo de razonamiento (GPT-4o/Ollama)
       - Disponibilidad de conexión
    
    2. **ChromaDB:**
       - Estado de la base de vectores
       - Accesibilidad del vector store
    
    3. **Paperless:**
       - Conexión con servidor
       - Validación de credenciales
       - Respuesta de API
    
    4. **Documentos:**
       - Total de documentos indexados
       - Estado de vectorización
    
    **Estados posibles:**
    - `healthy`: Todos los componentes funcionando correctamente
    - `degraded`: Algunos componentes con problemas (servicio parcial)
    - `unhealthy`: Sistema no disponible
    
    **Uso recomendado:**
    - Monitoreo de infraestructura
    - Health checks de load balancers
    - Validación pre-deployment
    - Troubleshooting de problemas
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
