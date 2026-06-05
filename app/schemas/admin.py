"""Schemas del panel de administración de parámetros operativos."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CampoConfig(BaseModel):
    """Metadato + valor actual de un parámetro editable."""
    clave: str
    etiqueta: str
    tipo: str = Field(..., description="bool | int | str | enum")
    valor: Any = None
    hot: bool = Field(..., description="True si se aplica sin reiniciar el servicio")
    descripcion: Optional[str] = None
    opciones: Optional[List[str]] = None
    min: Optional[int] = None
    max: Optional[int] = None


class ConfigResponse(BaseModel):
    """Listado de parámetros operativos editables (sin secretos)."""
    campos: List[CampoConfig]


class ActualizarConfigRequest(BaseModel):
    """Cambios a aplicar: { CLAVE: valor }. Solo se aceptan claves de la allowlist."""
    cambios: Dict[str, Any] = Field(..., description="Mapa clave→valor de parámetros editables.")

    class Config:
        json_schema_extra = {
            "example": {"cambios": {"CONSULTAS_MAX_FILAS": 1000, "LLM_PROVIDER": "opencode", "VOICE_ENABLED": True}}
        }


class ActualizarConfigResponse(BaseModel):
    """Resultado de aplicar cambios."""
    aplicados_en_caliente: List[str]
    requieren_reinicio: List[str]
    comando_reinicio: Optional[str] = None
    mensaje: str
