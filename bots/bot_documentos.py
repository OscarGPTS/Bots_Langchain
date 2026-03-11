"""Bot de Documentos - Búsqueda inteligente en Paperless con IA"""
import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Cargar variables de entorno
load_dotenv()

PAPERLESS_URL = os.getenv('PAPERLESS_URL')
PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
OLLAMA_URL = os.getenv('OLLAMA_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi4-mini:latest')


class BotDocumentos:
    """Bot especializado en búsqueda de documentos con IA"""
    
    def __init__(self):
        self.llm = None
        self._inicializar_ia()
        self._verificar_paperless()
    
    def _inicializar_ia(self):
        """Inicializar modelo de IA"""
        try:
            self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_URL,
                temperature=0.3
            )
            self.llm.invoke([HumanMessage(content="Test")])
            print(f"✅ IA conectada: {OLLAMA_MODEL}")
        except Exception as e:
            print(f"⚠️ IA no disponible: {e}")
            self.llm = None
    
    def _verificar_paperless(self):
        """Verificar conexión con Paperless"""
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            print("❌ Error: PAPERLESS_URL o PAPERLESS_TOKEN no configurados en .env")
            print("   Ejecuta: python scripts/generar_token_paperless.py")
            return
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/",
                headers=headers,
                params={'page_size': 1},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            total = data.get('count', 0)
            print(f"✅ Paperless conectado: {total} documentos disponibles\n")
        except Exception as e:
            print(f"⚠️ Error al conectar con Paperless: {e}\n")
    
    def buscar_documentos(self, query: str, max_resultados: int = 10) -> List[Dict]:
        """Buscar documentos en Paperless con fallback inteligente"""
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            return []
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            params = {
                'page_size': max_resultados,
                'ordering': '-created'
            }
            
            # Solo agregar query si no está vacía
            if query.strip():
                params['query'] = query
            
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            resultados = data.get('results', [])
            
            # Si no encontró nada con la query, intentar estrategias de fallback
            if not resultados and query.strip():
                # Estrategia 1: Buscar en títulos
                params_all = {
                    'page_size': 100,
                    'ordering': '-created'
                }
                response_all = requests.get(
                    f"{PAPERLESS_URL}/api/documents/",
                    headers=headers,
                    params=params_all,
                    timeout=10
                )
                response_all.raise_for_status()
                all_docs = response_all.json().get('results', [])
                
                # Filtrar por título (búsqueda case-insensitive)
                query_lower = query.lower()
                resultados = [
                    doc for doc in all_docs
                    if query_lower in doc.get('title', '').lower()
                ][:max_resultados]
                
                # Estrategia 2: Si sigue sin resultados, buscar con palabras clave
                if not resultados:
                    import re
                    # Extraer palabras significativas (más de 3 letras, sin números solos)
                    palabras = re.findall(r'\b[a-záéíóúñ]{4,}\b', query.lower())
                    
                    if palabras:
                        # Buscar documentos que contengan cualquiera de las palabras clave
                        for palabra in palabras[:3]:  # Máximo 3 palabras clave
                            for doc in all_docs:
                                titulo = doc.get('title', '').lower()
                                if palabra in titulo and doc not in resultados:
                                    resultados.append(doc)
                                    if len(resultados) >= max_resultados:
                                        break
                            if resultados:
                                break
            
            return resultados
        
        except Exception as e:
            print(f"⚠️ Error al buscar documentos: {e}")
            return []
    
    def obtener_contenido(self, documento_id: int) -> str:
        """Obtener contenido OCR de un documento"""
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            return ""
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            
            # Obtener detalles del documento con contenido
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/{documento_id}/",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            doc = response.json()
            return doc.get('content', '')
        
        except Exception as e:
            print(f"⚠️ Error al obtener contenido: {e}")
            return ""
    
    def procesar(self, pregunta: str) -> str:
        """Procesar pregunta sobre documentos"""
        pregunta_lower = pregunta.lower()
        
        # Comandos especiales
        if 'listar' in pregunta_lower or 'lista' in pregunta_lower:
            if 'recientes' in pregunta_lower or 'últimos' in pregunta_lower:
                return self._listar_recientes()
        
        # Comando: analizar documento por ID
        if 'analiza documento' in pregunta_lower or 'analizar documento' in pregunta_lower:
            import re
            match = re.search(r'documento\s+(\d+)', pregunta_lower)
            if match:
                doc_id = int(match.group(1))
                # Extraer pregunta adicional si existe
                pregunta_extra = re.sub(r'analiz[ar]?\s+documento\s+\d+\s*', '', pregunta, flags=re.IGNORECASE).strip()
                return self.analizar_documento(doc_id, pregunta_extra)
        
        # Limpiar la query: remover palabras de comando al inicio
        import re
        query = pregunta
        # Remover palabras de comando al inicio de la frase
        query = re.sub(r'^\s*(busca|buscar|encuentra|encontrar|dame|muestra|mostrar)(\s+en)?\s+', '', query, flags=re.IGNORECASE)
        
        # Debug: mostrar la query limpia
        if query != pregunta:
            print(f"🔧 Query limpia: '{query}'")
        
        # Buscar documentos relevantes
        print("🔍 Buscando documentos relevantes...")
        documentos = self.buscar_documentos(query, max_resultados=5)
        
        if not documentos:
            # Último intento: buscar con palabras clave más generales
            import re
            # Palabras comunes a ignorar
            palabras_ignorar = {'que', 'dice', 'sobre', 'cual', 'donde', 'como', 'cuando', 'quien', 'quienes', 'para', 'desde', 'hasta', 'entre'}
            
            palabras_clave = [
                p for p in re.findall(r'\b[a-záéíóúñ]{4,}\b', query.lower())
                if p not in palabras_ignorar
            ]
            
            if palabras_clave and len(palabras_clave) > 0:
                # Intentar con las primeras palabras significativas
                query_reducida = ' '.join(palabras_clave[:2])
                print(f"🔍 Reintentando con términos clave: '{query_reducida}'")
                documentos = self.buscar_documentos(query_reducida, max_resultados=5)
        
        if not documentos:
            return self._sin_resultados(query)
        
        print(f"📄 Encontrados {len(documentos)} documentos")
        
        # Usar IA para analizar contenido
        if self.llm:
            return self._analizar_con_ia(pregunta, documentos)
        else:
            return self._respuesta_simple(documentos)
    
    def _analizar_con_ia(self, pregunta: str, documentos: List[Dict]) -> str:
        """Analizar documentos con IA"""
        try:
            # Preparar contexto con contenido de documentos
            contexto = f"Pregunta del usuario: {pregunta}\n\n"
            contexto += f"Documentos encontrados ({len(documentos)}):\n\n"
            
            for i, doc in enumerate(documentos[:3], 1):
                contexto += f"--- Documento {i}: {doc.get('title')} ---\n"
                contexto += f"Creado: {doc.get('created')}\n"
                
                # Obtener contenido OCR
                print(f"📖 Leyendo contenido del documento {i}...")
                contenido = self.obtener_contenido(doc.get('id'))
                
                if contenido:
                    # Limitar contenido para no saturar la IA
                    contenido_limitado = contenido[:2000]
                    contexto += f"Contenido (extracto):\n{contenido_limitado}\n\n"
                else:
                    contexto += "Contenido: No disponible\n\n"
            
            # Pedir a la IA que analice
            prompt = f"""{contexto}

Basándote en los documentos anteriores:
1. Responde directamente a la pregunta del usuario
2. Si encuentras información relevante, cítala y menciona en qué documento está
3. Si no encuentras información específica, indica qué contienen los documentos
4. Sé conciso pero informativo

Respuesta:"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            respuesta_ia = response.content.strip()
            
            # Agregar lista de documentos al final
            resultado = f"🤖 {respuesta_ia}\n\n"
            resultado += "─" * 60 + "\n"
            resultado += f"📚 Documentos analizados:\n\n"
            
            for doc in documentos[:3]:
                resultado += f"📄 {doc.get('title')}\n"
                resultado += f"   📅 {doc.get('created')}\n"
                resultado += f"   🔗 ID: {doc.get('id')}\n\n"
            
            return resultado
        
        except Exception as e:
            print(f"⚠️ Error al analizar con IA: {e}")
            return self._respuesta_simple(documentos)
    
    def _respuesta_simple(self, documentos: List[Dict]) -> str:
        """Respuesta sin IA"""
        respuesta = f"✅ Encontrados {len(documentos)} documentos:\n\n"
        
        for doc in documentos[:10]:
            respuesta += f"📄 {doc.get('title')}\n"
            respuesta += f"   📅 Creado: {doc.get('created')}\n"
            respuesta += f"   🔗 ID: {doc.get('id')}\n"
            
            # Agregar tags si existen
            tags = doc.get('tags', [])
            if tags:
                respuesta += f"   🏷️  Tags: {', '.join(str(t) for t in tags)}\n"
            
            respuesta += "\n"
        
        if len(documentos) > 10:
            respuesta += f"... y {len(documentos) - 10} documentos más.\n"
        
        respuesta += "\n💡 Usa la IA para analizar el contenido específico de un documento.\n"
        
        return respuesta
    
    def _listar_recientes(self) -> str:
        """Listar documentos recientes"""
        print("📋 Obteniendo documentos recientes...")
        documentos = self.buscar_documentos("", max_resultados=10)
        
        if not documentos:
            return "❌ No se encontraron documentos"
        
        respuesta = f"📚 Últimos {len(documentos)} documentos:\n\n"
        
        for i, doc in enumerate(documentos, 1):
            respuesta += f"{i}. 📄 {doc.get('title')}\n"
            respuesta += f"   📅 {doc.get('created')}\n"
            respuesta += f"   🔗 ID: {doc.get('id')}\n\n"
        
        return respuesta
    
    def _sin_resultados(self, pregunta: str) -> str:
        """Mensaje cuando no hay resultados"""
        if self.llm:
            try:
                prompt = f"""El usuario buscó: "{pregunta}"

No se encontraron documentos en Paperless.

Genera una respuesta útil que:
1. Sugiera reformular la búsqueda con términos más generales
2. Mencione que puede listar todos los documentos con "lista documentos recientes"
3. Recomiende usar palabras clave del documento

Sé breve."""

                response = self.llm.invoke([HumanMessage(content=prompt)])
                return "🤖 " + response.content.strip()
            except:
                pass
        
        return """❌ No se encontraron documentos.

💡 Sugerencias:
  - Usa términos más generales
  - Intenta con palabras clave del título
  - Escribe "lista documentos recientes" para ver todos
  - Ejemplo: "busca contratos", "política de vacaciones"
"""
    
    def analizar_documento(self, doc_id: int, pregunta: str = "") -> str:
        """Analizar un documento específico por ID"""
        if not self.llm:
            return "❌ IA no disponible"
        
        print(f"📖 Obteniendo documento {doc_id}...")
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/{doc_id}/",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            doc = response.json()
            
            contenido = doc.get('content', '')
            
            if not contenido:
                return f"❌ El documento '{doc.get('title')}' no tiene contenido OCR disponible"
            
            print("🤖 Analizando contenido...")
            
            if pregunta:
                prompt = f"""Documento: {doc.get('title')}
Contenido:
{contenido[:3000]}

Pregunta del usuario: {pregunta}

Responde la pregunta basándote en el contenido del documento. Si la información no está en el documento, indícalo."""
            else:
                prompt = f"""Documento: {doc.get('title')}
Contenido:
{contenido[:3000]}

Genera un resumen ejecutivo de este documento destacando:
1. Tema principal
2. Puntos clave
3. Información importante

Sé conciso."""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            resultado = f"📄 Documento: {doc.get('title')}\n"
            resultado += f"📅 Creado: {doc.get('created')}\n\n"
            resultado += "─" * 60 + "\n\n"
            resultado += response.content.strip()
            
            return resultado
        
        except Exception as e:
            return f"❌ Error al analizar documento: {e}"


def main():
    print("🤖 Bot de Documentos - Búsqueda Inteligente en Paperless")
    print("=" * 60)
    print(f"📡 Paperless: {PAPERLESS_URL}")
    print(f"🧠 IA: {OLLAMA_MODEL}\n")
    
    bot = BotDocumentos()
    
    print("=" * 60)
    print("\n💡 Ejemplos de consultas:")
    print("  - Busca documentos sobre contratos")
    print("  - ¿Qué dice la política de vacaciones?")
    print("  - Resume el documento sobre seguridad")
    print("  - Lista documentos recientes")
    print("  - Analiza el documento ID 123")
    print("\nEscribe 'salir' para terminar.\n")
    
    while True:
        try:
            pregunta = input("📝 Consulta: ").strip()
            
            if not pregunta:
                continue
            
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            # Comandos especiales
            if pregunta.lower().startswith('analiza'):
                # Ejemplo: "analiza documento 123"
                partes = pregunta.split()
                if len(partes) >= 3 and partes[2].isdigit():
                    doc_id = int(partes[2])
                    pregunta_doc = ' '.join(partes[3:]) if len(partes) > 3 else ""
                    print("\n🤖 Procesando...\n")
                    respuesta = bot.analizar_documento(doc_id, pregunta_doc)
                else:
                    respuesta = "❌ Formato: 'analiza documento [ID] [pregunta opcional]'"
            else:
                print("\n🤖 Procesando...\n")
                respuesta = bot.procesar(pregunta)
            
            print(respuesta)
            print("\n" + "-" * 60 + "\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
