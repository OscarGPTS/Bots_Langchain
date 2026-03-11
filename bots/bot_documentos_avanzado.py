"""
Bot de Documentos Avanzado - Con ChromaDB y OpenAI
===================================================
Sistema inteligente de búsqueda y análisis de documentos con:
- ChromaDB para vectorización persistente
- Soporte dual: OpenAI (cloud) y Ollama (local)
- Optimización de costos con Context Caching
- Dos modos: Consulta Rápida y Razonamiento Profundo
- Monitor de gasto de tokens
"""

import os
import re
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# LangChain imports
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.callbacks import get_openai_callback

# Cargar variables de entorno
load_dotenv()

# Configuración
PAPERLESS_URL = os.getenv('PAPERLESS_URL')
PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
OLLAMA_URL = os.getenv('OLLAMA_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi4-mini:latest')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_RAPIDO = os.getenv('OPENAI_MODEL_RAPIDO', 'gpt-4o-mini')
OPENAI_MODEL_RAZONAMIENTO = os.getenv('OPENAI_MODEL_RAZONAMIENTO', 'gpt-4o')

# ChromaDB Configuration
CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '150'))

# Flag para usar IA local o cloud
LOCALIA = os.getenv('LOCALIA', 'true').lower() == 'true'


class BotDocumentosAvanzado:
    """Bot avanzado con ChromaDB y soporte dual OpenAI/Ollama"""
    
    def __init__(self):
        """Inicializar el bot"""
        self.vector_store = None
        self.embeddings = None
        self.llm_rapido = None
        self.llm_razonamiento = None
        self.text_splitter = None
        self.documentos_indexados = set()
        
        print("="*70)
        print("🚀 Inicializando Bot de Documentos Avanzado")
        print("="*70)
        
        # Inicializar componentes
        self._inicializar_embeddings()
        self._inicializar_vector_store()
        self._inicializar_modelos_ia()
        self._inicializar_text_splitter()
        self._cargar_documentos_paperless()
        
        print("\n✅ Bot inicializado correctamente")
        print("="*70)
    
    def _inicializar_embeddings(self):
        """Inicializar embeddings según configuración"""
        print(f"\n📊 Inicializando embeddings (LOCALIA={LOCALIA})...")
        
        try:
            if LOCALIA:
                # Usar Ollama local
                self.embeddings = OllamaEmbeddings(
                    base_url=OLLAMA_URL,
                    model=OLLAMA_MODEL
                )
                print(f"✅ Embeddings Ollama ({OLLAMA_MODEL}) inicializados")
            else:
                # Usar OpenAI
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY no configurada en .env")
                
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                print("✅ OpenAI Embeddings inicializados")
        
        except Exception as e:
            print(f"❌ Error al inicializar embeddings: {e}")
            raise
    
    def _inicializar_vector_store(self):
        """Inicializar ChromaDB con persistencia local"""
        print(f"\n🗄️  Inicializando ChromaDB en: {CHROMA_DB_PATH}")
        
        try:
            # Crear directorio si no existe
            os.makedirs(CHROMA_DB_PATH, exist_ok=True)
            
            # Usar colección diferente según proveedor (evita conflictos de dimensiones)
            collection_name = "docs_ollama" if LOCALIA else "docs_openai"
            
            # Inicializar Chroma con persistencia
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_DB_PATH
            )
            
            # Contar documentos existentes
            collection = self.vector_store._collection
            count = collection.count()
            
            print(f"✅ ChromaDB inicializado (Colección: {collection_name}, {count} vectores almacenados)")
        
        except Exception as e:
            print(f"❌ Error al inicializar ChromaDB: {e}")
            raise
    
    def _inicializar_modelos_ia(self):
        """Inicializar modelos de IA según configuración"""
        print(f"\n🤖 Inicializando modelos de IA...")
        
        try:
            if LOCALIA:
                # Usar Ollama local (mismo modelo para ambos)
                self.llm_rapido = ChatOllama(
                    model=OLLAMA_MODEL,
                    base_url=OLLAMA_URL,
                    temperature=0.2
                )
                self.llm_razonamiento = ChatOllama(
                    model=OLLAMA_MODEL,
                    base_url=OLLAMA_URL,
                    temperature=0.5
                )
                print(f"✅ Modelos Ollama ({OLLAMA_MODEL}) inicializados")
            
            else:
                # Usar OpenAI con dos modelos diferentes
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY no configurada en .env")
                
                # Modelo rápido para consultas simples
                self.llm_rapido = ChatOpenAI(
                    model=OPENAI_MODEL_RAPIDO,
                    temperature=0.2,
                    openai_api_key=OPENAI_API_KEY
                )
                
                # Modelo con razonamiento para análisis complejos
                self.llm_razonamiento = ChatOpenAI(
                    model=OPENAI_MODEL_RAZONAMIENTO,
                    temperature=0.5,
                    openai_api_key=OPENAI_API_KEY,
                    model_kwargs={
                        "reasoning_effort": "medium"  # GPT-5 reasoning
                    }
                )
                
                print(f"✅ Modelos OpenAI inicializados:")
                print(f"   - Rápido: {OPENAI_MODEL_RAPIDO}")
                print(f"   - Razonamiento: {OPENAI_MODEL_RAZONAMIENTO}")
        
        except Exception as e:
            print(f"❌ Error al inicializar modelos IA: {e}")
            raise
    
    def _inicializar_text_splitter(self):
        """Inicializar divisor de texto con 15% overlap"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        print(f"\n✂️  Text Splitter: {CHUNK_SIZE} tokens, {CHUNK_OVERLAP} overlap ({CHUNK_OVERLAP/CHUNK_SIZE*100:.0f}%)")
    
    def _cargar_documentos_paperless(self):
        """Cargar y vectorizar documentos desde Paperless"""
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            print("\n⚠️  Paperless no configurado, omitiendo carga de documentos")
            return
        
        print(f"\n📥 Conectando con Paperless: {PAPERLESS_URL}")
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            
            # Obtener todos los documentos
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/",
                headers=headers,
                params={'page_size': 100},
                timeout=10
            )
            response.raise_for_status()
            
            documentos = response.json().get('results', [])
            print(f"📄 Encontrados {len(documentos)} documentos en Paperless")
            
            # Procesar documentos nuevos
            documentos_nuevos = 0
            for doc in documentos:
                doc_id = str(doc.get('id'))
                
                # Verificar si ya está indexado en ChromaDB
                try:
                    results = self.vector_store.get(
                        where={"doc_id": doc_id}
                    )
                    if results and results.get('ids'):
                        self.documentos_indexados.add(doc_id)
                        continue
                except:
                    pass
                
                # Documento nuevo, indexar
                if self._indexar_documento(doc, headers):
                    documentos_nuevos += 1
                    self.documentos_indexados.add(doc_id)
            
            if documentos_nuevos > 0:
                print(f"✅ Indexados {documentos_nuevos} documentos nuevos")
            else:
                print("✅ Todos los documentos ya están indexados")
        
        except Exception as e:
            print(f"⚠️  Error al cargar documentos: {e}")
    
    def _indexar_documento(self, doc: Dict, headers: Dict) -> bool:
        """Indexar un documento en ChromaDB"""
        try:
            doc_id = doc.get('id')
            title = doc.get('title', 'Sin título')
            
            # Obtener contenido OCR
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/{doc_id}/",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            content = response.json().get('content', '')
            if not content:
                return False
            
            # Dividir en chunks
            chunks = self.text_splitter.split_text(content)
            
            # Crear documentos con metadata
            documents = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "doc_id": str(doc_id),
                    "title": title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created": doc.get('created', ''),
                    "tags": ','.join(str(t) for t in doc.get('tags', [])),
                    "correspondent": doc.get('correspondent_name', '')
                }
                
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                )
            
            # Agregar a ChromaDB
            self.vector_store.add_documents(documents)
            
            print(f"   ✅ Indexado: {title} ({len(chunks)} chunks)")
            return True
        
        except Exception as e:
            print(f"   ❌ Error indexando documento {doc_id}: {e}")
            return False
    
    def buscar_semantica(
        self,
        query: str,
        k: int = 3,
        filtros: Optional[Dict] = None
    ) -> List[Document]:
        """
        Búsqueda semántica en ChromaDB
        
        Args:
            query: Consulta del usuario
            k: Número de chunks a recuperar
            filtros: Filtros de metadata (ej: {"tags": "contrato"})
        """
        try:
            if filtros:
                # Búsqueda con filtros de metadata
                results = self.vector_store.similarity_search(
                    query,
                    k=k,
                    filter=filtros
                )
            else:
                # Búsqueda sin filtros
                results = self.vector_store.similarity_search(query, k=k)
            
            return results
        
        except Exception as e:
            print(f"⚠️  Error en búsqueda semántica: {e}")
            return []
    
    def consulta_rapida(
        self,
        pregunta: str,
        filtros: Optional[Dict] = None
    ) -> Tuple[str, Optional[Dict]]:
        """
        Modo Consulta Rápida - Respuestas directas
        Usa GPT-4o-mini (OpenAI) o Ollama con solo 3 chunks
        
        Args:
            pregunta: Pregunta del usuario
            filtros: Filtros opcionales de metadata
        
        Returns:
            (respuesta, estadísticas)
        """
        print(f"\n{'='*70}")
        print("⚡ MODO: Consulta Rápida")
        print(f"{'='*70}")
        
        # Búsqueda semántica (solo 3 chunks más relevantes)
        print(f"🔍 Buscando: {pregunta}")
        chunks = self.buscar_semantica(pregunta, k=3, filtros=filtros)
        
        if not chunks:
            return "❌ No se encontraron documentos relevantes para tu consulta.", None
        
        print(f"📄 Encontrados {len(chunks)} fragmentos relevantes")
        
        # Construir contexto
        contexto = "\n\n".join([
            f"[Documento: {doc.metadata.get('title')}]\n{doc.page_content}"
            for doc in chunks
        ])
        
        # Prompt optimizado para consulta rápida
        prompt = f"""Responde esta pregunta de forma directa y concisa basándote ÚNICAMENTE en la información proporcionada.

Contexto de documentos:
{contexto}

Pregunta: {pregunta}

Respuesta directa:"""
        
        # Invocar modelo con monitoreo de costos
        if LOCALIA:
            # Ollama (sin callback de costos)
            try:
                response = self.llm_rapido.invoke([HumanMessage(content=prompt)])
                respuesta = response.content
                
                # Incluir información de documentos fuente
                respuesta += "\n\n" + "─"*60
                respuesta += "\n📚 Documentos consultados:\n"
                for doc in chunks:
                    respuesta += f"\n📄 {doc.metadata.get('title')}"
                    respuesta += f" (Creado: {doc.metadata.get('created', 'N/A')[:10]})"
                
                return respuesta, None
            
            except Exception as e:
                return f"❌ Error al procesar consulta: {e}", None
        
        else:
            # OpenAI con monitoreo de costos
            try:
                with get_openai_callback() as cb:
                    response = self.llm_rapido.invoke([HumanMessage(content=prompt)])
                    respuesta = response.content
                    
                    # Estadísticas de uso
                    stats = {
                        "tokens_entrada": cb.prompt_tokens,
                        "tokens_salida": cb.completion_tokens,
                        "tokens_total": cb.total_tokens,
                        "costo_usd": cb.total_cost
                    }
                    
                    # Incluir información de documentos fuente
                    respuesta += "\n\n" + "─"*60
                    respuesta += "\n📚 Documentos consultados:\n"
                    for doc in chunks:
                        respuesta += f"\n📄 {doc.metadata.get('title')}"
                        respuesta += f" (Creado: {doc.metadata.get('created', 'N/A')[:10]})"
                    
                    # Mostrar estadísticas
                    respuesta += "\n\n" + "─"*60
                    respuesta += "\n💰 Estadísticas de uso:"
                    respuesta += f"\n   📥 Tokens entrada: {stats['tokens_entrada']}"
                    respuesta += f"\n   📤 Tokens salida: {stats['tokens_salida']}"
                    respuesta += f"\n   💵 Costo estimado: ${stats['costo_usd']:.6f} USD"
                    
                    return respuesta, stats
            
            except Exception as e:
                return f"❌ Error al procesar consulta: {e}", None
    
    def razonamiento_profundo(
        self,
        pregunta: str,
        filtros: Optional[Dict] = None,
        k: int = 10
    ) -> Tuple[str, Optional[Dict]]:
        """
        Modo Razonamiento Profundo - Análisis complejos
        Usa GPT-4o (OpenAI) con reasoning_effort="medium" o Ollama
        
        Args:
            pregunta: Pregunta compleja del usuario
            filtros: Filtros opcionales de metadata
            k: Número de chunks a analizar (mayor contexto)
        
        Returns:
            (respuesta, estadísticas)
        """
        print(f"\n{'='*70}")
        print("🧠 MODO: Razonamiento Profundo")
        print(f"{'='*70}")
        
        # Búsqueda semántica (más chunks para análisis)
        print(f"🔍 Buscando: {pregunta}")
        chunks = self.buscar_semantica(pregunta, k=k, filtros=filtros)
        
        if not chunks:
            return "❌ No se encontraron documentos relevantes para tu análisis.", None
        
        print(f"📄 Encontrados {len(chunks)} fragmentos relevantes")
        
        # Construir contexto enriquecido
        contexto = ""
        docs_unicos = {}
        
        for doc in chunks:
            doc_id = doc.metadata.get('doc_id')
            if doc_id not in docs_unicos:
                docs_unicos[doc_id] = {
                    'title': doc.metadata.get('title'),
                    'created': doc.metadata.get('created'),
                    'chunks': []
                }
            docs_unicos[doc_id]['chunks'].append(doc.page_content)
        
        for doc_id, data in docs_unicos.items():
            contexto += f"\n{'='*60}\n"
            contexto += f"Documento: {data['title']}\n"
            contexto += f"Fecha: {data['created'][:10]}\n"
            contexto += f"{'='*60}\n\n"
            contexto += "\n\n".join(data['chunks'])
            contexto += "\n\n"
        
        # Prompt para razonamiento profundo
        prompt = f"""Analiza cuidadosamente la información proporcionada y responde la pregunta con un razonamiento detallado.

Documentos disponibles:
{contexto}

Pregunta para analizar:
{pregunta}

Proporciona un análisis estructurado que incluya:
1. Información clave encontrada
2. Razonamiento lógico
3. Conclusiones basadas en evidencia
4. Recomendaciones si aplica

Análisis:"""
        
        # Invocar modelo con monitoreo
        if LOCALIA:
            # Ollama
            try:
                response = self.llm_razonamiento.invoke([HumanMessage(content=prompt)])
                respuesta = response.content
                
                # Incluir información de documentos fuente
                respuesta += "\n\n" + "─"*60
                respuesta += "\n📚 Documentos analizados:\n"
                for doc_id, data in docs_unicos.items():
                    respuesta += f"\n📄 {data['title']}"
                    respuesta += f" ({len(data['chunks'])} fragmentos)"
                
                return respuesta, None
            
            except Exception as e:
                return f"❌ Error al procesar análisis: {e}", None
        
        else:
            # OpenAI con reasoning y monitoreo
            try:
                with get_openai_callback() as cb:
                    response = self.llm_razonamiento.invoke([HumanMessage(content=prompt)])
                    respuesta = response.content
                    
                    # Estadísticas de uso (incluye tokens de razonamiento)
                    stats = {
                        "tokens_entrada": cb.prompt_tokens,
                        "tokens_salida": cb.completion_tokens,
                        "tokens_total": cb.total_tokens,
                        "costo_usd": cb.total_cost
                    }
                    
                    # Incluir información de documentos fuente
                    respuesta += "\n\n" + "─"*60
                    respuesta += "\n📚 Documentos analizados:\n"
                    for doc_id, data in docs_unicos.items():
                        respuesta += f"\n📄 {data['title']}"
                        respuesta += f" ({len(data['chunks'])} fragmentos)"
                    
                    # Mostrar estadísticas
                    respuesta += "\n\n" + "─"*60
                    respuesta += "\n💰 Estadísticas de uso (con razonamiento):"
                    respuesta += f"\n   📥 Tokens entrada: {stats['tokens_entrada']}"
                    respuesta += f"\n   📤 Tokens salida: {stats['tokens_salida']}"
                    respuesta += f"\n   🧠 Tokens razonamiento: incluidos en entrada"
                    respuesta += f"\n   💵 Costo estimado: ${stats['costo_usd']:.6f} USD"
                    
                    return respuesta, stats
            
            except Exception as e:
                return f"❌ Error al procesar análisis: {e}", None
    
    def procesar(self, pregunta: str) -> str:
        """
        Procesar pregunta del usuario (entrada principal)
        Detecta automáticamente qué modo usar
        """
        # Comandos especiales
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            return "¡Hasta luego!"
        
        if 'ayuda' in pregunta.lower() or 'help' in pregunta.lower():
            return self._ayuda()
        
        # Detectar si es consulta simple o análisis complejo
        palabras_clave_analisis = [
            'analiza', 'compara', 'resume', 'tendencia', 'patrón',
            'relación', 'evolución', 'historia', 'explicación detallada',
            'razonamiento', 'conclusión', 'evalúa', 'por qué'
        ]
        
        es_analisis = any(palabra in pregunta.lower() for palabra in palabras_clave_analisis)
        
        # Detectar filtros de metadata en la pregunta
        filtros = self._extraer_filtros(pregunta)
        
        if es_analisis:
            respuesta, _ = self.razonamiento_profundo(pregunta, filtros)
            return respuesta
        else:
            respuesta, _ = self.consulta_rapida(pregunta, filtros)
            return respuesta
    
    def _extraer_filtros(self, pregunta: str) -> Optional[Dict]:
        """Extraer filtros de metadata de la pregunta"""
        filtros = {}
        
        # Detectar fechas (ej: "documentos de 2026")
        match_año = re.search(r'\b(20\d{2})\b', pregunta)
        if match_año:
            año = match_año.group(1)
            filtros['created'] = {'$regex': f'^{año}'}
        
        # Detectar tags (ej: "contratos", "facturas")
        tags_comunes = ['contrato', 'factura', 'política', 'reporte', 'manual']
        for tag in tags_comunes:
            if tag in pregunta.lower():
                if 'tags' not in filtros:
                    filtros['tags'] = {'$regex': tag}
        
        return filtros if filtros else None
    
    def _ayuda(self) -> str:
        """Mostrar ayuda del bot"""
        return f"""
{'='*70}
🤖 BOT DE DOCUMENTOS AVANZADO - AYUDA
{'='*70}

📊 CONFIGURACIÓN ACTUAL:
   - Modo: {'🏠 Local (Ollama)' if LOCALIA else '☁️  Cloud (OpenAI)'}
   - Base de datos: ChromaDB en {CHROMA_DB_PATH}
   - Documentos indexados: {len(self.documentos_indexados)}
   - Chunk size: {CHUNK_SIZE} tokens

🎯 MODOS DE USO:

⚡ Consulta Rápida (automático para preguntas simples):
   - "¿Cuál es el monto de la factura X?"
   - "¿Qué dice el contrato sobre pagos?"
   - "Encuentra el documento sobre seguridad"

🧠 Razonamiento Profundo (automático para análisis):
   - "Analiza la tendencia de gastos de los últimos 6 meses"
   - "Compara los contratos A y B"
   - "Resume los puntos clave del proyecto X"

🔍 FILTROS AUTOMÁTICOS:
   - Por año: "documentos de 2026"
   - Por tipo: usa palabras como "contrato", "factura", etc.

💡 COMANDOS:
   - 'ayuda' o 'help': Mostrar esta ayuda
   - 'salir' o 'exit': Cerrar el bot

{'='*70}
"""


def main():
    """Función principal - Modo interactivo"""
    bot = BotDocumentosAvanzado()
    
    print("\n" + bot._ayuda())
    print("\n💬 Escribe tu consulta o 'salir' para terminar\n")
    
    while True:
        try:
            pregunta = input("📝 Consulta: ").strip()
            
            if not pregunta:
                continue
            
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            print("\n🤖 Procesando...\n")
            respuesta = bot.procesar(pregunta)
            print(f"\n{respuesta}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
