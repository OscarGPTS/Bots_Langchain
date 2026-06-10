"""Factory del LLM de chat para el módulo de consultas.

Proveedor y modelo configurables a medida para este módulo:
  - CONSULTAS_LLM_PROVIDER: ollama | openai | opencode | auto (hereda LLM_PROVIDER).
  - CONSULTAS_LLM_MODEL: sobreescribe el modelo del proveedor elegido
    ("auto"/vacío = modelo default del proveedor, p.ej. OPENCODE_MODEL).

Así los bots RAG y el generador de SQL pueden usar modelos distintos (p.ej.
opencode/deepseek para SQL estructurado y ollama para chat) sin duplicar
credenciales: estas siguen siendo las globales (OPENCODE_*, OPENAI_*, OLLAMA_*).
"""
from functools import lru_cache
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _modelo_override() -> Optional[str]:
    """Modelo fijado para consultas, o None si aplica el default del proveedor."""
    modelo = (settings.CONSULTAS_LLM_MODEL or "").strip()
    if not modelo or modelo.lower() == "auto":
        return None
    return modelo


@lru_cache
def obtener_llm():
    """Devolver el chat model configurado (temperatura baja para SQL/intent)."""
    proveedor = settings.consultas_llm_provider
    modelo = _modelo_override()

    if proveedor == "ollama":
        return ChatOllama(
            model=modelo or settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_URL,
            temperature=0.0,
        )

    if proveedor == "opencode":
        if not (settings.OPENCODE_BASE_URL and settings.OPENCODE_API_KEY):
            raise ValueError("OpenCode requiere OPENCODE_BASE_URL y OPENCODE_API_KEY.")
        if not (modelo or settings.OPENCODE_MODEL):
            raise ValueError("Define OPENCODE_MODEL o CONSULTAS_LLM_MODEL.")
        return ChatOpenAI(
            model=modelo or settings.OPENCODE_MODEL,
            temperature=0.0,
            openai_api_key=settings.OPENCODE_API_KEY,
            base_url=settings.OPENCODE_BASE_URL,
        )

    # openai
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada.")
    return ChatOpenAI(
        model=modelo or settings.OPENAI_MODEL_RAPIDO,
        temperature=0.0,
        openai_api_key=settings.OPENAI_API_KEY,
    )
