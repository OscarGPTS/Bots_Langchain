"""Configuración central de la aplicación.

Única fuente de verdad para variables de entorno. Reemplaza los
`load_dotenv()` + `os.getenv(...)` dispersos por el código.
"""
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cargar el .env también en os.environ. pydantic-settings solo mapea los campos
# declarados; las variables DSN/URL arbitrarias que referencia rules.yaml
# (dsn_env/base_url_env) se leen con os.getenv y necesitan estar en el entorno.
#
# override=True => el .env es la fuente de verdad y PISA variables de entorno
# preexistentes (p.ej. una DB_USERNAME que quedó fijada en la sesión de la shell).
# Es lo esperado aquí: la configuración vive en .env (no se inyecta por systemd).
load_dotenv(override=True)


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
    # Nota: controla los EMBEDDINGS y la colección de ChromaDB. El modelo de chat
    # se elige con LLM_PROVIDER (ver abajo). Para usar OpenCode con embeddings
    # locales, mantener LOCALIA=true y LLM_PROVIDER=opencode.
    LOCALIA: bool = True

    # ===== Proveedor del LLM de chat (etapa de respuesta del RAG) =====
    # "auto" => deriva de LOCALIA (ollama si true, openai si false).
    # "ollama" | "openai" | "opencode".
    LLM_PROVIDER: str = "auto"

    # OpenCode Go (gateway compatible con la API de OpenAI)
    OPENCODE_BASE_URL: Optional[str] = None
    OPENCODE_API_KEY: Optional[str] = None
    OPENCODE_MODEL: Optional[str] = None

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

    # ===== Servidor API (desarrollo local) =====
    API_PORT: int = 8001

    # ===== Base de datos SQLite (opcional) =====
    DATABASE_PATH: str = "data/empresa.db"

    # ===== Voz (STT + TTS) =====
    VOICE_ENABLED: bool = False
    VOICE_BACKEND: str = "simple"          # qué bot RAG usa la voz: simple | avanzado
    # STT (voz -> texto)
    STT_PROVIDER: str = "local"            # local (faster-whisper) | openai
    WHISPER_MODEL: str = "small"           # tiny|base|small|medium|large-v3
    WHISPER_DEVICE: str = "cpu"            # cpu | cuda
    WHISPER_COMPUTE_TYPE: str = "int8"     # int8 (cpu) | float16 (gpu)
    STT_LANGUAGE: str = "es"
    VOICE_MAX_SECONDS: int = 60            # duración máxima de audio aceptada
    OPENAI_STT_MODEL: str = "whisper-1"    # whisper-1 | gpt-4o-transcribe | gpt-4o-mini-transcribe
    # TTS (texto -> voz)
    TTS_PROVIDER: str = "local"            # local (Piper) | openai
    PIPER_VOICE_PATH: str = "models/piper/es_MX.onnx"
    OPENAI_TTS_MODEL: str = "tts-1"        # tts-1 | tts-1-hd | gpt-4o-mini-tts
    OPENAI_TTS_VOICE: str = "nova"         # voz OpenAI (nova/shimmer/coral = femeninas)

    # ===== Módulo de Consultas a Datos (NL -> SQL / API REST) =====
    # Apagado por defecto. Consulta orígenes definidos en el catálogo de reglas.
    CONSULTAS_ENABLED: bool = False
    RULES_PATH: str = "config/rules.yaml"
    CONSULTAS_MAX_FILAS: int = 500       # tope global de filas devueltas (solo-lectura)
    CONSULTAS_SQL_TIMEOUT: int = 8       # segundos máx. de ejecución por consulta SQL
    CONSULTAS_REST_TIMEOUT: int = 10     # timeout para orígenes REST

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

    @property
    def chat_llm_provider(self) -> str:
        """Proveedor efectivo del LLM de chat: ollama | openai | opencode."""
        provider = (self.LLM_PROVIDER or "auto").lower()
        if provider == "auto":
            return "ollama" if self.LOCALIA else "openai"
        return provider


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
