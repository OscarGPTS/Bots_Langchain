"""Configuración central de la aplicación.

Única fuente de verdad para variables de entorno. Reemplaza los
`load_dotenv()` + `os.getenv(...)` dispersos por el código.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===== Paperless-ngx =====
    PAPERLESS_URL: Optional[str] = None
    PAPERLESS_TOKEN: Optional[str] = None

    # ===== Ollama (IA local) =====
    OLLAMA_URL: Optional[str] = None
    OLLAMA_MODEL: str = "phi4-mini:latest"

    # ===== OpenAI (IA cloud) =====
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_RAPIDO: str = "gpt-4o-mini"
    OPENAI_MODEL_RAZONAMIENTO: str = "gpt-4o"

    # true = Ollama (local, sin costo); false = OpenAI (cloud)
    LOCALIA: bool = True

    # ===== ChromaDB =====
    CHROMA_DB_PATH: str = "./chroma_db"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # Indexar todos los documentos al construir el bot (arranque de la app).
    # Por defecto False: la indexación se hace de forma explícita con
    # `scripts/indexar_docs.py` o el endpoint protegido `/reindexar`. Esto evita
    # que varios workers de Gunicorn indexen en paralelo contra la misma ChromaDB.
    INDEX_ON_STARTUP: bool = False

    # ===== API de RH (opcional) =====
    API_RH_URL: Optional[str] = None

    # ===== Base de datos SQLite (opcional) =====
    DATABASE_PATH: str = "data/empresa.db"

    # ===== Seguridad / operación =====
    # Token requerido para operaciones administrativas (p.ej. /reindexar).
    # Si está vacío, esos endpoints quedan deshabilitados (403).
    ADMIN_TOKEN: Optional[str] = None

    # Orígenes permitidos para CORS. "*" o lista separada por comas.
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_allow_credentials(self) -> bool:
        # No se pueden usar credenciales con comodín de orígenes.
        return self.cors_origins_list != ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
