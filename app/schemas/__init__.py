"""Schemas Pydantic para validación de requests y responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


# ========== Requests ==========

class QueryRequest(BaseModel):
    """Request para consultas generales del bot simple"""
    pregunta: str = Field(
        ..., 
        description="Pregunta o consulta sobre documentos de Paperless", 
        min_length=3,
        max_length=500
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "¿Qué dice el código de ética sobre integridad?"
            },
            "examples": [
                {
                    "pregunta": "Busca contratos de servicios de 2026"
                },
                {
                    "pregunta": "Resume la política de vacaciones"
                },
                {
                    "pregunta": "¿Quién es el corresponsal del documento 123?"
                }
            ]
        }


class QueryAvanzadaRequest(BaseModel):
    """Request para consulta rápida del bot avanzado (3 chunks)"""
    pregunta: str = Field(
        ..., 
        description="Pregunta del usuario (consultas directas y simples)", 
        min_length=3,
        max_length=500
    )
    filtros: Optional[Dict] = Field(
        None, 
        description="Filtros de metadata opcionales. Ejemplos: {'created': '2026'}, {'tags': 'contrato'}"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "¿Cuál es el horario de trabajo?",
                "filtros": {"created": "2026"}
            },
            "examples": [
                {
                    "pregunta": "¿Monto máximo de gastos sin autorización?"
                },
                {
                    "pregunta": "Encuentra facturas de enero",
                    "filtros": {"tags": "factura"}
                }
            ]
        }


class RazonamientoRequest(BaseModel):
    """Request para razonamiento profundo (análisis complejos con hasta 20 chunks)"""
    pregunta: str = Field(
        ..., 
        description="Pregunta compleja que requiere análisis profundo y razonamiento", 
        min_length=3,
        max_length=1000
    )
    filtros: Optional[Dict] = Field(
        None, 
        description="Filtros de metadata opcionales"
    )
    k: int = Field(
        10, 
        description="Número de chunks a analizar (más chunks = más contexto pero más lento)", 
        ge=1, 
        le=20
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "Analiza las políticas de vacaciones y compáralas con la legislación laboral",
                "k": 10
            },
            "examples": [
                {
                    "pregunta": "Compara los contratos de 2025 vs 2026 y resume los cambios principales",
                    "k": 15
                },
                {
                    "pregunta": "Explica la relación entre el código de ética y los procedimientos disciplinarios",
                    "filtros": {"tags": "politica"},
                    "k": 12
                }
            ]
        }


class BusquedaSemanticaRequest(BaseModel):
    """Request para búsqueda semántica"""
    query: str = Field(..., description="Consulta de búsqueda", min_length=3)
    k: int = Field(5, description="Número de resultados", ge=1, le=20)
    filtros: Optional[Dict] = Field(None, description="Filtros de metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "políticas de seguridad",
                "k": 5
            }
        }


class AnalyzeDocumentRequest(BaseModel):
    """Request para analizar documento por ID"""
    documento_id: int = Field(..., description="ID del documento en Paperless", gt=0)
    pregunta: Optional[str] = Field(None, description="Pregunta específica sobre el documento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documento_id": 1,
                "pregunta": "¿Cuáles son los puntos clave de este documento?"
            }
        }


# ========== Responses ==========

class QueryResponse(BaseModel):
    """Response para consultas (bot simple)"""
    respuesta: str = Field(
        ..., 
        description="Respuesta generada por el bot con información de documentos fuente"
    )
    tiempo_respuesta: float = Field(
        ..., 
        description="Tiempo de procesamiento en segundos"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": """El código de ética define la integridad como actuar con honestidad y transparencia en todas las actividades...

──────────────────────────────
📚 Documentos consultados:

📄 Código de Ética y Conducta (Creado: 2026-03-10)""",
                "tiempo_respuesta": 2.5
            }
        }


class QueryAvanzadaResponse(BaseModel):
    """Response para consultas del bot avanzado (con estadísticas opcionales)"""
    respuesta: str = Field(
        ..., 
        description="Respuesta generada con documentos fuente"
    )
    estadisticas: Optional[Dict] = Field(
        None, 
        description="Estadísticas de uso (solo OpenAI): tokens_entrada, tokens_salida, tokens_total, costo_usd"
    )
    tiempo_respuesta: float = Field(
        ..., 
        description="Tiempo total de procesamiento en segundos"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "El horario de trabajo estándar es de lunes a viernes de 8:00 a 17:00...",
                "estadisticas": {
                    "tokens_entrada": 150,
                    "tokens_salida": 80,
                    "tokens_total": 230,
                    "costo_usd": 0.00015
                },
                "tiempo_respuesta": 3.2
            },
            "description": "Las estadísticas solo se incluyen cuando se usa OpenAI. Con Ollama (local) será null."
        }


class DocumentoInfo(BaseModel):
    """Información de un documento (chunk)"""
    doc_id: str
    title: str
    chunk_index: int
    total_chunks: int
    created: str
    preview: str = Field(..., description="Preview del contenido")
    score: Optional[float] = Field(None, description="Score de similitud")


class DocumentoPaperless(BaseModel):
    """Documento completo de Paperless con URLs para preview y descarga"""
    id: int = Field(..., description="ID del documento en Paperless")
    title: str = Field(..., description="Título del documento")
    created: str = Field(..., description="Fecha de creación")
    modified: Optional[str] = Field(None, description="Fecha de modificación")
    content: Optional[str] = Field(None, description="Contenido (si se solicita)")
    archive_serial_number: Optional[int] = Field(None, description="Número de archivo")
    correspondent: Optional[int] = Field(None, description="ID del corresponsal")
    document_type: Optional[int] = Field(None, description="ID del tipo de documento")
    tags: Optional[List[int]] = Field(default_factory=list, description="IDs de tags")
    
    # URLs para frontend
    download_url: Optional[str] = Field(None, description="URL para descargar el documento original")
    preview_url: Optional[str] = Field(None, description="URL para preview/visualización del documento")
    thumbnail_url: Optional[str] = Field(None, description="URL para thumbnail (miniatura)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Código de Ética y Conducta",
                "created": "2026-03-10",
                "modified": "2026-03-11",
                "archive_serial_number": None,
                "correspondent": None,
                "document_type": 1,
                "tags": [],
                "download_url": "https://paperless.tech-energy.lat/api/documents/1/download/?token=abc123",
                "preview_url": "https://paperless.tech-energy.lat/api/documents/1/preview/?token=abc123",
                "thumbnail_url": "https://paperless.tech-energy.lat/api/documents/1/thumb/?token=abc123"
            }
        }


class DocumentosListResponse(BaseModel):
    """Response para lista de documentos con URLs para preview"""
    documentos: List[DocumentoPaperless]
    total: int = Field(..., description="Total de documentos")
    tiempo_respuesta: float = Field(..., description="Tiempo en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documentos": [
                    {
                        "id": 1,
                        "title": "Código de Ética",
                        "created": "2026-03-10",
                        "modified": "2026-03-11",
                        "tags": [],
                        "download_url": "https://paperless.tech-energy.lat/api/documents/1/download/?token=abc123",
                        "preview_url": "https://paperless.tech-energy.lat/api/documents/1/preview/?token=abc123",
                        "thumbnail_url": "https://paperless.tech-energy.lat/api/documents/1/thumb/?token=abc123"
                    }
                ],
                "total": 1,
                "tiempo_respuesta": 0.5
            },
            "description": """Las URLs incluidas permiten:
- **download_url**: Descargar el archivo original (PDF, imagen, etc.)
- **preview_url**: Mostrar preview del documento en navegador
- **thumbnail_url**: Cargar miniatura (para listados/grids)

✅ Las URLs ya incluyen el token de autenticación como query parameter (?token=XXX).
Puedes usarlas directamente sin configuración adicional:

```html
<img src="{thumbnail_url}" />
<a href="{download_url}">Descargar</a>
<iframe src="{preview_url}"></iframe>
```

⚠️ No expongas estas URLs públicamente (contienen tu token de acceso).
"""
        }
    

class BusquedaSemanticaResponse(BaseModel):
    """Response para búsqueda semántica"""
    resultados: List[DocumentoInfo]
    total: int = Field(..., description="Número de resultados encontrados")
    tiempo_respuesta: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "resultados": [
                    {
                        "doc_id": "3",
                        "title": "Código de Ética",
                        "chunk_index": 5,
                        "total_chunks": 20,
                        "created": "2026-03-10",
                        "preview": "La integridad se define como..."
                    }
                ],
                "total": 1,
                "tiempo_respuesta": 0.8
            }
        }


class DocumentoIndexado(BaseModel):
    """Documento indexado en ChromaDB"""
    doc_id: str
    title: str
    chunks: int
    fecha_indexacion: str


class StatsResponse(BaseModel):
    """Estadísticas del bot avanzado"""
    total_documentos: int
    total_vectores: int
    modo: str = Field(..., description="local (Ollama) o cloud (OpenAI)")
    modelo_rapido: str
    modelo_razonamiento: str
    documentos_indexados: List[DocumentoIndexado]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Estado del servicio")
    version: str
    timestamp: str
    ia_disponible: bool
    chromadb_disponible: bool
    paperless_conectado: bool
    total_documentos: int


class ErrorResponse(BaseModel):
    """Response de error"""
    error: str = Field(..., description="Mensaje de error")
    detalle: Optional[str] = Field(None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "No se encontraron documentos",
                "detalle": "La consulta no arrojó resultados"
            }
        }


class ReindexarResponse(BaseModel):
    """Response para reindexación"""
    mensaje: str
    documentos_nuevos: int
    documentos_actualizados: int
    tiempo_total: float


class VozResponse(BaseModel):
    """Response de consulta por voz (formato_respuesta=texto o ambos).

    Con `formato_respuesta=texto`, `audio_base64` es `null`.
    Con `formato_respuesta=ambos`, incluye el audio WAV de la respuesta en base64.
    (Con `formato_respuesta=audio` la respuesta es binaria `audio/wav`, no este JSON.)
    """
    pregunta_transcrita: str = Field(..., description="Texto transcrito del audio de entrada")
    respuesta: str = Field(..., description="Respuesta generada por el RAG")
    audio_base64: Optional[str] = Field(None, description="Audio WAV de la respuesta en base64 (solo formato=ambos)")
    tiempo_respuesta: float = Field(..., description="Tiempo total en segundos (STT + RAG + TTS)")

    class Config:
        json_schema_extra = {
            "example": {
                "pregunta_transcrita": "¿Qué dice el reglamento interno sobre el horario de trabajo?",
                "respuesta": "El horario de trabajo es de lunes a viernes de 8:00 a 17:00...",
                "audio_base64": "UklGRiQAAABXQVZFZm10IB...(WAV en base64)...",
                "tiempo_respuesta": 5.8,
            }
        }


class VozHealthResponse(BaseModel):
    """Estado de los componentes del módulo de voz."""
    voice_enabled: bool
    stt_provider: str
    tts_provider: str
    ffmpeg_disponible: bool
    faster_whisper_disponible: bool
    piper_disponible: bool
    voz_piper_existe: bool
    openai_disponible: bool
    backend_rag: str
    whisper_model: str

    class Config:
        json_schema_extra = {
            "example": {
                "voice_enabled": True,
                "stt_provider": "local",
                "tts_provider": "local",
                "ffmpeg_disponible": True,
                "faster_whisper_disponible": True,
                "piper_disponible": True,
                "voz_piper_existe": True,
                "openai_disponible": True,
                "backend_rag": "simple",
                "whisper_model": "small",
            }
        }
