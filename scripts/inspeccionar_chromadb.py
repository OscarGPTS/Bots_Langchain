"""
Script para inspeccionar el contenido de ChromaDB
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import chromadb

# Cargar variables de entorno
load_dotenv()

CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')

def inspeccionar_chromadb():
    """Inspeccionar todas las colecciones en ChromaDB"""
    print("="*70)
    print("🔍 INSPECTOR DE CHROMADB")
    print("="*70)
    print(f"\n📁 Ruta: {CHROMA_DB_PATH}\n")
    
    try:
        # Conectar a ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Listar todas las colecciones
        colecciones = client.list_collections()
        
        if not colecciones:
            print("⚠️  No hay colecciones en ChromaDB")
            return
        
        print(f"📚 Colecciones encontradas: {len(colecciones)}\n")
        
        for col in colecciones:
            print("="*70)
            print(f"📦 Colección: {col.name}")
            print("="*70)
            
            # Obtener información de la colección
            count = col.count()
            print(f"   📊 Total de vectores: {count}")
            
            if count > 0:
                # Obtener primeros documentos
                results = col.get(limit=5, include=['documents', 'metadatas'])
                
                print(f"\n   📄 Primeros {len(results['ids'])} documentos:\n")
                
                for i, (doc_id, doc, metadata) in enumerate(zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ), 1):
                    print(f"   {i}. ID: {doc_id[:50]}...")
                    if metadata:
                        print(f"      Título: {metadata.get('title', 'N/A')}")
                        print(f"      Doc ID: {metadata.get('doc_id', 'N/A')}")
                        print(f"      Chunk: {metadata.get('chunk_index', 'N/A')}/{metadata.get('total_chunks', 'N/A')}")
                        print(f"      Fecha: {metadata.get('created', 'N/A')[:10]}")
                    if doc:
                        preview = doc[:150].replace('\n', ' ')
                        print(f"      Preview: {preview}...")
                    print()
                
                # Estadísticas de documentos únicos
                if results['metadatas']:
                    doc_ids = set(m.get('doc_id') for m in results['metadatas'] if m)
                    print(f"   📋 Documentos únicos en esta muestra: {len(doc_ids)}")
                    for doc_id in doc_ids:
                        # Buscar título
                        titulo = next(
                            (m.get('title') for m in results['metadatas'] 
                             if m and m.get('doc_id') == doc_id),
                            'N/A'
                        )
                        print(f"      - Doc {doc_id}: {titulo}")
            
            print()
        
        # Resumen final
        print("="*70)
        print("📊 RESUMEN GENERAL")
        print("="*70)
        total_vectores = sum(col.count() for col in colecciones)
        print(f"   Total de colecciones: {len(colecciones)}")
        print(f"   Total de vectores: {total_vectores}")
        print()
        
    except Exception as e:
        print(f"❌ Error al inspeccionar ChromaDB: {e}")


def buscar_en_coleccion(nombre_coleccion: str, query: str):
    """Buscar documentos en una colección específica"""
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        coleccion = client.get_collection(name=nombre_coleccion)
        
        print(f"\n🔍 Buscando '{query}' en colección '{nombre_coleccion}'...\n")
        
        # Buscar (sin embeddings, solo busca en metadatos)
        results = coleccion.get(
            where={"title": {"$contains": query}},
            include=['documents', 'metadatas']
        )
        
        if not results['ids']:
            print("⚠️  No se encontraron resultados")
            return
        
        print(f"✅ Encontrados {len(results['ids'])} resultados:\n")
        
        for i, (doc_id, doc, metadata) in enumerate(zip(
            results['ids'], 
            results['documents'], 
            results['metadatas']
        ), 1):
            print(f"{i}. Título: {metadata.get('title', 'N/A')}")
            print(f"   Chunk: {metadata.get('chunk_index')}/{metadata.get('total_chunks')}")
            print(f"   Preview: {doc[:200]}...")
            print()
    
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Modo búsqueda
        if len(sys.argv) >= 3:
            nombre_col = sys.argv[1]
            query = " ".join(sys.argv[2:])
            buscar_en_coleccion(nombre_col, query)
        else:
            print("Uso para búsqueda: python inspeccionar_chromadb.py <coleccion> <query>")
    else:
        # Modo inspección
        inspeccionar_chromadb()
