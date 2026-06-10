"""Sincronización del contexto semántico desde sus repos fuente.

Los documentos de contexto se EDITAN en el repo del proyecto que documentan
(fuente de verdad) y aquí solo vive la copia de ingestión (`context/<origen>/`).
Este script copia las fuentes registradas en FUENTES y reindexa la colección.

Uso:
    python scripts/sincronizar_contexto.py               # copiar + indexar
    python scripts/sincronizar_contexto.py --solo-copiar # copiar sin indexar

Para registrar un documento nuevo: agregar su entrada a FUENTES
(destino relativo a context/ -> ruta absoluta del archivo fuente).
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Consolas Windows (cp1252) no soportan los emojis del output.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import settings

# destino (relativo a context/) -> fuente de verdad (ruta absoluta en el repo dueño)
FUENTES = {
    "cartera_db/CONTEXTO_GRAFICAS_DASHBOARD.md":
        r"C:\xampp\htdocs\GPT_Catera_Clientes2\docs\CONTEXTO_GRAFICAS_DASHBOARD.md",
}


def main():
    solo_copiar = "--solo-copiar" in sys.argv
    base = Path(settings.CONTEXT_PATH)

    print("\n" + "=" * 70)
    print("🔄 Sincronizando contexto desde los repos fuente")
    print("=" * 70)

    copiados, errores = 0, 0
    for destino_rel, fuente in FUENTES.items():
        origen = Path(fuente)
        destino = base / destino_rel
        if not origen.is_file():
            print(f"⚠️  No existe la fuente: {origen}  (se conserva la copia actual)")
            errores += 1
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.is_file() and destino.read_bytes() == origen.read_bytes():
            print(f"= Sin cambios: {destino_rel}")
            continue
        shutil.copyfile(origen, destino)
        print(f"📥 Copiado: {origen} -> {destino_rel}")
        copiados += 1

    if solo_copiar:
        print(f"\n✅ Copia terminada ({copiados} actualizado(s)). Indexa con scripts/indexar_contexto.py")
        sys.exit(0 if not errores else 1)

    if copiados == 0 and errores == 0:
        print("\n✅ Todo al día; no hace falta reindexar.")
        sys.exit(0)

    from app.services.consultas import contexto_rag

    try:
        stats = contexto_rag.indexar_directorio()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"📄 Archivos indexados: {stats['archivos']} · 🧩 Chunks: {stats['chunks']}")
    for err in stats["errores"]:
        print(f"⚠️  {err}")
    print("\n✅ SINCRONIZACIÓN COMPLETADA" if not (errores or stats["errores"]) else "\n⚠️ SINCRONIZACIÓN CON AVISOS")
    sys.exit(0 if not (errores or stats["errores"]) else 1)


if __name__ == "__main__":
    main()
