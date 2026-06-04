"""Schemas Pydantic del módulo de Consultas a Datos (NL -> SQL / API REST).

La respuesta es un **objeto estructurado**: el frontend decide cómo pintarlo
(texto, tabla o —fase 2— gráfico). La IA solo lee datos; nunca escribe.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TipoSalida(str, Enum):
    """Tipo de representación sugerida para el frontend."""
    texto = "texto"
    tabla = "tabla"
    grafico = "grafico"  # Reservado para fase 2 (Chart.js en el frontend)


# ========== Request ==========

class ConsultaRequest(BaseModel):
    """Petición de consulta a un origen de datos."""
    consulta: str = Field(
        ...,
        description="Lo que pide el usuario en lenguaje natural (texto; la voz se transcribe antes).",
        min_length=3,
        max_length=1000,
    )
    origen: str = Field(
        ...,
        description="Clave del origen a consultar (definido en el catálogo de reglas).",
        min_length=1,
        max_length=64,
    )
    formato: Optional[TipoSalida] = Field(
        None,
        description="Fuerza el tipo de salida. Si se omite, la IA lo decide (texto/tabla).",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "consulta": "Dame una tabla de todos los usuarios registrados desde el 1 de enero de 2026",
                "origen": "ventas_db",
            }
        }


# ========== Response ==========

class TablaPayload(BaseModel):
    """Datos tabulares para pintar una tabla en el frontend."""
    columnas: List[str] = Field(..., description="Nombres de columna en orden.")
    filas: List[List[Any]] = Field(..., description="Filas; cada fila alinea con `columnas`.")
    total_filas: int = Field(..., description="Filas devueltas (tras aplicar el tope).")
    truncado: bool = Field(False, description="True si se alcanzó el tope de filas (`max_filas`).")


class GraficoPayload(BaseModel):
    """Especificación de gráfico (FASE 2). Hueco reservado; hoy siempre null."""
    tipo_grafico: str = Field(..., description="bar | line | pie | ... (fase 2)")
    etiquetas: List[Any] = Field(default_factory=list)
    series: List[Dict[str, Any]] = Field(default_factory=list)


class ConsultaMeta(BaseModel):
    """Metadatos de trazabilidad y auditoría de la consulta."""
    origen_tipo: str = Field(..., description="sql_mysql | rest_api")
    consulta_generada: Optional[str] = Field(
        None, description="SQL ejecutado o endpoint REST consultado (auditoría)."
    )
    candidatos: List[str] = Field(
        default_factory=list, description="Tablas/recursos candidatos detectados por las keys."
    )
    advertencias: List[str] = Field(default_factory=list)


class ConsultaResponse(BaseModel):
    """Respuesta estructurada de una consulta a datos."""
    origen: str
    tipo: TipoSalida = Field(..., description="texto | tabla | grafico")
    titulo: Optional[str] = Field(None, description="Título legible de la respuesta.")
    texto: Optional[str] = Field(None, description="Respuesta/resumen en lenguaje natural.")
    tabla: Optional[TablaPayload] = Field(None, description="Datos tabulares (si tipo=tabla).")
    grafico: Optional[GraficoPayload] = Field(None, description="Spec de gráfico (fase 2).")
    meta: ConsultaMeta
    tiempo_respuesta: float = Field(..., description="Tiempo total en segundos.")

    class Config:
        json_schema_extra = {
            "example": {
                "origen": "ventas_db",
                "tipo": "tabla",
                "titulo": "Usuarios registrados desde 2026-01-01",
                "texto": "Se encontraron 42 usuarios registrados a partir del 1 de enero de 2026.",
                "tabla": {
                    "columnas": ["id", "nombre", "email", "fecha_ingreso"],
                    "filas": [[1, "Ana López", "ana@x.com", "2026-02-03"]],
                    "total_filas": 42,
                    "truncado": False,
                },
                "grafico": None,
                "meta": {
                    "origen_tipo": "sql_mysql",
                    "consulta_generada": "SELECT id, nombre, email, fecha_ingreso FROM usuarios WHERE fecha_ingreso >= '2026-01-01' LIMIT 500",
                    "candidatos": ["usuarios"],
                    "advertencias": [],
                },
                "tiempo_respuesta": 1.8,
            }
        }


class OrigenInfo(BaseModel):
    """Resumen de un origen disponible (para listar el catálogo)."""
    clave: str
    tipo: str
    descripcion: Optional[str] = None
    tablas_o_recursos: List[str] = Field(default_factory=list)


class ConsultasHealthResponse(BaseModel):
    """Estado del módulo de consultas."""
    consultas_enabled: bool
    rules_cargado: bool
    rules_path: str
    total_origenes: int
    origenes: List[OrigenInfo] = Field(default_factory=list)
    error_rules: Optional[str] = None
