"""Indexación del contexto semántico del módulo de Consultas en ChromaDB.

Indexa los Markdown de `context/<origen>/` (catálogos de vistas, glosarios de
negocio) en la colección propia del módulo de consultas. Idempotente: re-ejecutar
reemplaza los chunks de cada archivo en vez de duplicarlos.

Uso:
    python scripts/indexar_contexto.py            # indexa todo context/
    python scripts/indexar_contexto.py <carpeta>  # otra carpeta base
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Consolas Windows (cp1252) no soportan los emojis del output.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.consultas import contexto_rag


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else None

    print("\n" + "=" * 70)
    print("🔧 Indexando contexto del módulo de Consultas")
    print("=" * 70)

    try:
        stats = contexto_rag.indexar_directorio(ruta)
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"📄 Archivos indexados: {stats['archivos']}")
    print(f"🧩 Chunks generados:   {stats['chunks']}")
    for err in stats["errores"]:
        print(f"⚠️  {err}")

    info = contexto_rag.estado()
    print(f"📊 Colección '{info['coleccion']}': {info['vectores']} vectores")

    print("\n" + "=" * 70)
    print("✅ INDEXACIÓN COMPLETADA" if not stats["errores"] else "⚠️ INDEXACIÓN CON ERRORES")
    print("=" * 70)
    sys.exit(0 if not stats["errores"] else 1)


if __name__ == "__main__":
    main()
