"""Contexto semántico (RAG) del módulo de consultas.

Indexa los documentos Markdown de `context/<origen>/` en una colección propia de
ChromaDB y recupera los bloques relevantes para inyectarlos al prompt NL→SQL como
sección «Vistas del sistema». Cada bloque del MD es autocontenido (ver
`context/README.md`), por lo que un chunk recuperado funciona sin el resto del
documento.

Degrada en silencio: si ChromaDB/embeddings no están disponibles o la colección
está vacía, `recuperar_contexto` devuelve "" y la consulta sigue funcionando solo
con rules.yaml.
"""
import os
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Colección separada por proveedor de embeddings (evita conflictos de dimensiones).
_NOMBRE_COLECCION = "contexto_consultas_ollama" if settings.LOCALIA else "contexto_consultas_openai"

# Chunks por petición de embeddings al indexar (ver indexar_directorio).
_LOTE_INDEXADO = 8

_vector_store = None          # caché del Chroma inicializado
_vector_store_error = False   # True si la inicialización ya falló (no reintentar por consulta)


def _crear_embeddings():
    """Embeddings según LOCALIA (mismo criterio que los bots RAG)."""
    if settings.LOCALIA:
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(base_url=settings.OLLAMA_URL, model=settings.OLLAMA_MODEL)

    from langchain_openai import OpenAIEmbeddings

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no configurada en .env")
    return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY, model="text-embedding-3-small")


def _obtener_vector_store():
    """Chroma de la colección de contexto (lazy, cacheado). None si no disponible."""
    global _vector_store, _vector_store_error

    if _vector_store is not None:
        return _vector_store
    if _vector_store_error:
        return None

    try:
        from langchain_chroma import Chroma

        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        _vector_store = Chroma(
            collection_name=_NOMBRE_COLECCION,
            embedding_function=_crear_embeddings(),
            persist_directory=settings.CHROMA_DB_PATH,
        )
        return _vector_store
    except Exception as e:  # noqa: BLE001
        _vector_store_error = True
        logger.warning("Contexto RAG no disponible (%s); las consultas siguen solo con rules.yaml", e)
        return None


def recuperar_contexto(consulta: str, origen_clave: str, k: Optional[int] = None) -> str:
    """Top-k chunks del contexto del origen relevantes para la consulta, o "".

    Filtra por metadato `origen` para no mezclar contexto de otros proyectos.
    Nunca lanza: cualquier fallo se registra y se devuelve cadena vacía.
    """
    if not settings.CONSULTAS_RAG_ENABLED:
        return ""

    store = _obtener_vector_store()
    if store is None:
        return ""

    try:
        docs = store.similarity_search(
            consulta,
            k=k or settings.CONSULTAS_RAG_TOP_K,
            filter={"origen": origen_clave},
        )
        return "\n\n".join(d.page_content.strip() for d in docs if d.page_content)
    except Exception as e:  # noqa: BLE001
        logger.warning("Fallo al recuperar contexto RAG para '%s': %s", origen_clave, e)
        return ""


def indexar_directorio(ruta_base: Optional[str] = None) -> Dict:
    """Indexar `context/<origen>/*.md` en la colección (idempotente por archivo).

    Antes de agregar los chunks de un archivo se eliminan los existentes con el
    mismo metadato `archivo`, así re-ejecutar el script reemplaza en vez de duplicar.
    Devuelve estadísticas {archivos, chunks, errores}.
    """
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    store = _obtener_vector_store()
    if store is None:
        raise RuntimeError("ChromaDB/embeddings no disponibles; revisa la configuración (.env).")

    base = Path(ruta_base or settings.CONTEXT_PATH)
    if not base.is_dir():
        raise RuntimeError(f"No existe la carpeta de contexto: {base.resolve()}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    stats = {"archivos": 0, "chunks": 0, "errores": []}
    for ruta_md in sorted(base.glob("*/*.md")):
        origen = ruta_md.parent.name  # carpeta = clave del origen en rules.yaml
        rel = ruta_md.relative_to(base).as_posix()
        try:
            texto = ruta_md.read_text(encoding="utf-8")
            trozos = splitter.split_text(texto)

            # Reemplazo idempotente: borrar los chunks previos de este archivo.
            try:
                store._collection.delete(where={"archivo": rel})
            except Exception:  # noqa: BLE001 -- colección nueva/sin coincidencias
                pass

            documentos = [
                Document(page_content=t, metadata={"origen": origen, "archivo": rel, "chunk": i})
                for i, t in enumerate(trozos)
            ]
            # Lotes pequeños: una petición de embeddings con decenas de chunks puede
            # exceder el timeout de un Ollama remoto detrás de proxy (Cloudflare 524).
            for i in range(0, len(documentos), _LOTE_INDEXADO):
                store.add_documents(documentos[i : i + _LOTE_INDEXADO])
            stats["archivos"] += 1
            stats["chunks"] += len(documentos)
            logger.info("Indexado %s: %d chunks (origen=%s)", rel, len(documentos), origen)
        except Exception as e:  # noqa: BLE001
            stats["errores"].append(f"{rel}: {e}")
            logger.error("Error al indexar %s: %s", rel, e)

    return stats


def estado() -> Dict:
    """Estado de la colección de contexto (para health/diagnóstico)."""
    store = _obtener_vector_store()
    vectores = None
    if store is not None:
        try:
            vectores = store._collection.count()
        except Exception:  # noqa: BLE001
            pass
    return {
        "rag_enabled": settings.CONSULTAS_RAG_ENABLED,
        "coleccion": _NOMBRE_COLECCION,
        "disponible": store is not None,
        "vectores": vectores,
        "context_path": settings.CONTEXT_PATH,
        "top_k": settings.CONSULTAS_RAG_TOP_K,
    }
