"""Schemas Pydantic para validación de requests y responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


# ========== Requests ==========

class QueryRequest(BaseModel):
    """Request para consultas generales"""
    pregunta: str = Field(..., description="Pregunta o consulta del usuario", min_length=3)
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "¿Qué dice el código de ética sobre integridad?"
            }
        }


class QueryAvanzadaRequest(BaseModel):
    """Request para consulta rápida del bot avanzado"""
    pregunta: str = Field(..., description="Pregunta del usuario", min_length=3)
    filtros: Optional[Dict] = Field(None, description="Filtros de metadata (año, tags)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "¿Cuál es el horario de trabajo?",
                "filtros": {"created": "2026"}
            }
        }


class RazonamientoRequest(BaseModel):
    """Request para razonamiento profundo"""
    pregunta: str = Field(..., description="Pregunta compleja para análisis", min_length=3)
    filtros: Optional[Dict] = Field(None, description="Filtros de metadata")
    k: int = Field(10, description="Número de chunks a analizar", ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "pregunta": "Analiza las políticas de vacaciones y compáralas con la legislación",
                "k": 10
            }
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
    """Response para consultas"""
    respuesta: str = Field(..., description="Respuesta generada por el bot")
    tiempo_respuesta: float = Field(..., description="Tiempo de procesamiento en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "El código de ética define la integridad como...",
                "tiempo_respuesta": 2.5
            }
        }


class QueryAvanzadaResponse(BaseModel):
    """Response para consultas del bot avanzado"""
    respuesta: str = Field(..., description="Respuesta generada")
    estadisticas: Optional[Dict] = Field(None, description="Estadísticas de uso (tokens, costos)")
    tiempo_respuesta: float = Field(..., description="Tiempo en segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "respuesta": "El horario de trabajo es...",
                "estadisticas": {
                    "tokens_entrada": 150,
                    "tokens_salida": 80,
                    "costo_usd": 0.00015
                },
                "tiempo_respuesta": 3.2
            }
        }


class DocumentoInfo(BaseModel):
    """Información de un documento"""
    doc_id: str
    title: str
    chunk_index: int
    total_chunks: int
    created: str
    preview: str = Field(..., description="Preview del contenido")
    

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
