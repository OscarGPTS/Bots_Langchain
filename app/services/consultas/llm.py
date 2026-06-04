"""Factory del LLM de chat para el módulo de consultas.

Reutiliza la misma configuración del proyecto (LLM_PROVIDER: ollama | openai |
opencode) que el bot avanzado, sin duplicar la lógica de credenciales.
"""
from functools import lru_cache

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache
def obtener_llm():
    """Devolver el chat model configurado (temperatura baja para SQL/intent)."""
    proveedor = settings.chat_llm_provider

    if proveedor == "ollama":
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_URL,
            temperature=0.0,
        )

    if proveedor == "opencode":
        if not (settings.OPENCODE_BASE_URL and settings.OPENCODE_API_KEY and settings.OPENCODE_MODEL):
            raise ValueError("OpenCode requiere OPENCODE_BASE_URL, OPENCODE_API_KEY y OPENCODE_MODEL.")
        return ChatOpenAI(
            model=settings.OPENCODE_MODEL,
            temperature=0.0,
            openai_api_key=settings.OPENCODE_API_KEY,
            base_url=settings.OPENCODE_BASE_URL,
        )

    # openai
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada.")
    return ChatOpenAI(
        model=settings.OPENAI_MODEL_RAPIDO,
        temperature=0.0,
        openai_api_key=settings.OPENAI_API_KEY,
    )
