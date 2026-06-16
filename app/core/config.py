"""Configuración central de la aplicación.

Única fuente de verdad para variables de entorno. Reemplaza los
`load_dotenv()` + `os.getenv(...)` dispersos por el código.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del proyecto (carpeta que contiene .env, config/, context/, ...), calculada
# desde la ubicación de ESTE archivo (app/core/config.py -> parents[2]). Anclar a la
# raíz —y no al CWD del proceso— evita que el .env y los archivos de config "no se
# encuentren" cuando el servicio arranca desde otro directorio (systemd/gunicorn/docker).
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Cargar el .env también en os.environ. pydantic-settings solo mapea los campos
# declarados; las variables DSN/URL arbitrarias que referencia rules.yaml
# (dsn_env/base_url_env) se leen con os.getenv y necesitan estar en el entorno.
#
# override=True => el .env es la fuente de verdad y PISA variables de entorno
# preexistentes (p.ej. una DB_USERNAME que quedó fijada en la sesión de la shell).
# Es lo esperado aquí: la configuración vive en .env (no se inyecta por systemd).
# Ruta ABSOLUTA al .env de la raíz: independiente del directorio de arranque.
load_dotenv(PROJECT_ROOT / ".env", override=True)


class Settings(BaseSettings):
    """Configuración leída de variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===== Identidad del bot/aplicación =====
    # Nombre global del asistente. Se usa en la API (título/health), logs y respuestas.
    APP_NAME: str = "EVIA"

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
    # DEFAULT: opencode (gateway con deepseek). Si faltan credenciales de OpenCode
    # se degrada automáticamente según LOCALIA (ver chat_llm_provider).
    # "auto" => deriva de LOCALIA (ollama si true, openai si false).
    # "ollama" | "openai" | "opencode".
    LLM_PROVIDER: str = "opencode"

    # OpenCode Go (gateway compatible con la API de OpenAI). Proveedor por defecto
    # del chat; solo la API key es secreta y vive en .env.
    OPENCODE_BASE_URL: Optional[str] = "https://opencode.ai/zen/go/v1"
    OPENCODE_API_KEY: Optional[str] = None
    OPENCODE_MODEL: Optional[str] = "deepseek-v4-flash"

    # ===== Embeddings (RAG) =====
    # Modelo de embeddings DEDICADO (recomendado: nomic-embed-text en Ollama).
    # Si OLLAMA_EMBED_MODEL no se define, se usa OLLAMA_MODEL (compatibilidad con
    # las colecciones existentes de los bots). Solo lo consume el contexto RAG de
    # consultas; los bots de documentos conservan su comportamiento actual.
    OLLAMA_EMBED_MODEL: Optional[str] = None
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

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

    # Contexto semántico (RAG) de consultas: documentos en context/<origen>/*.md
    # indexados con scripts/indexar_contexto.py. Si la colección está vacía o
    # ChromaDB no responde, las consultas degradan a solo rules.yaml.
    CONSULTAS_RAG_ENABLED: bool = True
    CONSULTAS_RAG_TOP_K: int = 3         # chunks inyectados al prompt NL->SQL
    CONTEXT_PATH: str = "context"        # carpeta base del contexto por origen

    # LLM específico del módulo de consultas (NL->SQL). Permite usar un modelo
    # distinto al de los bots (p.ej. opencode/deepseek para SQL y ollama para chat).
    # "auto" => hereda LLM_PROVIDER global. CONSULTAS_LLM_MODEL sobreescribe el
    # modelo del proveedor elegido ("auto"/vacío = default del proveedor).
    CONSULTAS_LLM_PROVIDER: str = "auto"
    CONSULTAS_LLM_MODEL: Optional[str] = None

    # ===== Seguridad / operación =====
    # Token requerido para operaciones administrativas (p.ej. /reindexar).
    # Si está vacío, esos endpoints quedan deshabilitados (403).
    ADMIN_TOKEN: Optional[str] = None

    # Orígenes permitidos para CORS. "*" o lista separada por comas.
    CORS_ORIGINS: str = "*"

    @field_validator(
        "RULES_PATH", "CHROMA_DB_PATH", "CONTEXT_PATH", "DATABASE_PATH", "PIPER_VOICE_PATH",
        mode="after",
    )
    @classmethod
    def _ruta_absoluta(cls, valor: str) -> str:
        """Resolver rutas relativas contra la raíz del proyecto (no contra el CWD).

        Las rutas de archivo/carpeta de config (rules.yaml, context/, chroma_db, ...)
        se anclan a PROJECT_ROOT para que el servicio las encuentre aunque arranque
        desde otro directorio. Las rutas ya absolutas se respetan tal cual.
        """
        if not valor:
            return valor
        p = Path(valor)
        return str(p if p.is_absolute() else (PROJECT_ROOT / p).resolve())

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
        """Proveedor efectivo del LLM de chat: ollama | openai | opencode.

        Si el proveedor es opencode pero faltan sus credenciales (instalación
        nueva sin OPENCODE_API_KEY), degrada según LOCALIA para no tumbar los
        bots al arrancar.
        """
        provider = (self.LLM_PROVIDER or "auto").lower()
        if provider == "auto":
            return "ollama" if self.LOCALIA else "openai"
        if provider == "opencode" and not (self.OPENCODE_BASE_URL and self.OPENCODE_API_KEY):
            return "ollama" if self.LOCALIA else "openai"
        return provider

    @property
    def consultas_llm_provider(self) -> str:
        """Proveedor efectivo del LLM de consultas ('auto' hereda el global)."""
        provider = (self.CONSULTAS_LLM_PROVIDER or "auto").lower()
        if provider == "auto":
            return self.chat_llm_provider
        return provider

    @property
    def embeddings_model(self) -> str:
        """Modelo de embeddings efectivo según LOCALIA (con override dedicado)."""
        if self.LOCALIA:
            return self.OLLAMA_EMBED_MODEL or self.OLLAMA_MODEL
        return self.OPENAI_EMBED_MODEL

    def resumen_ia(self) -> dict:
        """Mapa de proveedor/modelo de IA efectivos por módulo (para `/` y `/health`).

        Refleja la configuración VIGENTE en settings. El bot avanzado congela su
        proveedor al arrancar: si se cambió en caliente sin reiniciar, lo real es
        lo del último arranque.
        """

        def _modelo_chat(proveedor: str, override: Optional[str] = None) -> Optional[str]:
            if override and override.strip() and override.strip().lower() != "auto":
                return override.strip()
            if proveedor == "ollama":
                return self.OLLAMA_MODEL
            if proveedor == "opencode":
                return self.OPENCODE_MODEL
            return self.OPENAI_MODEL_RAPIDO

        chat = self.chat_llm_provider
        consultas = self.consultas_llm_provider
        return {
            "bot_simple": {"proveedor": "ollama", "modelo": self.OLLAMA_MODEL},
            "bot_avanzado": {"proveedor": chat, "modelo": _modelo_chat(chat)},
            "consultas": {
                "proveedor": consultas,
                "modelo": _modelo_chat(consultas, self.CONSULTAS_LLM_MODEL),
            },
            "embeddings": {
                "proveedor": "ollama" if self.LOCALIA else "openai",
                "bots_documentos": self.OLLAMA_MODEL if self.LOCALIA else "text-embedding-3-small",
                "contexto_consultas": self.embeddings_model,
            },
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
