"""Bot General - Consulta RH y Paperless usando IA"""
import os
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Cargar variables de entorno
load_dotenv()

API_RH_URL = os.getenv('API_RH_URL')
PAPERLESS_URL = os.getenv('PAPERLESS_URL')
PAPERLESS_TOKEN = os.getenv('PAPERLESS_TOKEN')
OLLAMA_URL = os.getenv('OLLAMA_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi4-mini:latest')


class BotGeneral:
    """Bot inteligente que consulta RH y Paperless"""
    
    def __init__(self):
        self.usuarios_rh = []
        self.llm = None
        self._inicializar_ia()
        self._cargar_rh()
    
    def _inicializar_ia(self):
        """Inicializar modelo de IA"""
        try:
            self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_URL,
                temperature=0.3
            )
            # Test de conexión
            self.llm.invoke([HumanMessage(content="Hola")])
            print(f"✅ IA conectada: {OLLAMA_MODEL}")
        except Exception as e:
            print(f"⚠️ IA no disponible: {e}")
            print("   El bot funcionará sin IA")
    
    def _cargar_rh(self):
        """Cargar datos de RH"""
        try:
            response = requests.get(f"{API_RH_URL}/users", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.usuarios_rh = data.get('data', [])
            print(f"✅ {len(self.usuarios_rh)} empleados cargados")
        except Exception as e:
            print(f"⚠️ No se pudo cargar datos de RH: {e}")
    
    def buscar_empleados(self, termino: str) -> List[Dict]:
        """Buscar empleados por nombre, departamento o área"""
        termino = termino.lower()
        resultados = []
        
        for usuario in self.usuarios_rh:
            # Buscar en nombre
            if termino in usuario.get('nombre_completo', '').lower():
                resultados.append(usuario)
                continue
            
            # Buscar en departamento
            depto = usuario.get('departamento', {})
            if termino in depto.get('nombre', '').lower():
                resultados.append(usuario)
                continue
            
            # Buscar en área
            area = usuario.get('area', {})
            if termino in area.get('nombre', '').lower():
                resultados.append(usuario)
                continue
        
        return resultados
    
    def buscar_documentos(self, termino: str, max_resultados: int = 5) -> List[Dict]:
        """Buscar documentos en Paperless"""
        if not PAPERLESS_URL or not PAPERLESS_TOKEN:
            return []
        
        try:
            headers = {'Authorization': f'Token {PAPERLESS_TOKEN}'}
            params = {'query': termino, 'page_size': max_resultados}
            
            response = requests.get(
                f"{PAPERLESS_URL}/api/documents/",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
        
        except Exception as e:
            print(f"⚠️ Error al buscar en Paperless: {e}")
            return []
    
    def procesar(self, pregunta: str) -> str:
        """Procesar pregunta usando IA para decidir qué fuentes consultar"""
        pregunta_lower = pregunta.lower()
        
        # Responder preguntas estadísticas de RH
        if any(palabra in pregunta_lower for palabra in ['cuántos', 'cuantos', 'total']):
            if 'empleado' in pregunta_lower or 'usuario' in pregunta_lower or 'trabajador' in pregunta_lower:
                if 'departamento' in pregunta_lower:
                    return self._estadisticas_departamento()
                elif 'área' in pregunta_lower or 'area' in pregunta_lower:
                    return self._estadisticas_area()
                else:
                    activos = sum(1 for u in self.usuarios_rh if u.get('activo', False))
                    return f"📊 Total: {len(self.usuarios_rh)} empleados ({activos} activos)"
        
        # Análisis simple para decidir qué buscar
        es_sobre_rh = any(palabra in pregunta_lower for palabra in [
            'empleado', 'trabajador', 'persona', 'departamento', 'área',
            'quién', 'quien', 'equipo', 'staff', 'busca', 'buscar'
        ])
        
        es_sobre_docs = any(palabra in pregunta_lower for palabra in [
            'documento', 'archivo', 'pdf', 'contrato', 'factura',
            'reporte', 'informe', 'acta', 'política'
        ])
        
        # Buscar en RH
        resultados_rh = []
        if es_sobre_rh or not es_sobre_docs:
            # Extraer términos de búsqueda
            palabras = pregunta.split()
            for i, palabra in enumerate(palabras):
                if len(palabra) > 3 and palabra.lower() not in ['sobre', 'llamado', 'busca']:
                    temp_resultados = self.buscar_empleados(palabra.strip('¿?.,'))
                    if temp_resultados:
                        resultados_rh = temp_resultados
                        break
        
        # Buscar en Paperless
        resultados_docs = []
        if es_sobre_docs:
            resultados_docs = self.buscar_documentos(pregunta)
        
        # Si encontramos resultados, usar IA para respuesta natural
        if self.llm and (resultados_rh or resultados_docs):
            return self._responder_con_ia(pregunta, resultados_rh, resultados_docs)
        
        # Si no hay resultados Y tenemos IA, intentar búsqueda inteligente
        if not resultados_rh and not resultados_docs and self.llm:
            return self._busqueda_inteligente(pregunta)
        
        # Respuesta sin IA o sin búsqueda inteligente
        return self._responder_directo(resultados_rh, resultados_docs, pregunta)
    
    def _responder_con_ia(self, pregunta: str, resultados_rh: List[Dict], 
                          resultados_docs: List[Dict]) -> str:
        """Generar respuesta usando IA"""
        try:
            # Preparar contexto
            contexto = {"pregunta": pregunta}
            
            if resultados_rh:
                contexto["empleados"] = []
                for u in resultados_rh[:5]:
                    contexto["empleados"].append({
                        "nombre": u.get('nombre_completo'),
                        "puesto": u.get('puesto', {}).get('nombre'),
                        "departamento": u.get('departamento', {}).get('nombre'),
                        "email": u.get('email'),
                        "telefono": u.get('telefono')
                    })
            
            if resultados_docs:
                contexto["documentos"] = []
                for d in resultados_docs[:5]:
                    contexto["documentos"].append({
                        "titulo": d.get('title'),
                        "contenido_extracto": d.get('content', '')[:200],
                        "fecha": d.get('created')
                    })
            
            prompt = f"""Pregunta del usuario: {pregunta}

Datos encontrados:
{json.dumps(contexto, ensure_ascii=False, indent=2)}

Responde de forma directa y concisa. No uses frases como "con base en los datos proporcionados".
Si hay múltiples resultados, menciona cuántos encontraste y destaca los más relevantes."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            respuesta = response.content.strip()
            
            # Agregar detalles formateados
            resultado_final = respuesta + "\n\n"
            
            if resultados_rh:
                resultado_final += "📋 Detalles de empleados:\n"
                for u in resultados_rh[:5]:
                    resultado_final += f"  • {u.get('nombre_completo')} - {u.get('puesto', {}).get('nombre', 'N/A')}\n"
                    resultado_final += f"    📧 {u.get('email', 'N/A')}\n"
            
            if resultados_docs:
                resultado_final += "\n📄 Documentos relacionados:\n"
                for d in resultados_docs[:5]:
                    resultado_final += f"  • {d.get('title')} ({d.get('created', 'N/A')})\n"
            
            return resultado_final
        
        except Exception as e:
            print(f"⚠️ Error de IA: {e}")
            return self._responder_directo(resultados_rh, resultados_docs, pregunta)
    
    def _busqueda_inteligente(self, pregunta: str) -> str:
        """Usar IA para entender la pregunta y buscar información"""
        try:
            # Pedir a la IA que analice la pregunta
            prompt = f"""Analiza esta pregunta del usuario: "{pregunta}"

Tengo acceso a:
- Base de datos de {len(self.usuarios_rh)} empleados con: nombre, departamento, área, puesto, email
- Sistema de documentos Paperless

Extrae los términos clave para buscar. Responde SOLO con términos de búsqueda separados por comas.
Ejemplos:
- "dime sobre el ingeniero juan" → juan, ingeniero
- "quien trabaja en finanzas" → finanzas
- "empleados del area tecnica" → técnica, área

Términos de búsqueda:"""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            terminos = response.content.strip()
            
            print(f"🔍 IA sugiere buscar: {terminos}")
            
            # Buscar con los términos extraídos
            resultados_rh = []
            resultados_docs = []
            
            for termino in terminos.split(','):
                termino = termino.strip().lower()
                if len(termino) > 2:
                    # Buscar en RH
                    temp_rh = self.buscar_empleados(termino)
                    if temp_rh and not resultados_rh:
                        resultados_rh = temp_rh
                    
                    # Buscar en documentos si parece búsqueda de docs
                    if any(palabra in pregunta.lower() for palabra in ['documento', 'archivo', 'pdf']):
                        temp_docs = self.buscar_documentos(termino)
                        if temp_docs and not resultados_docs:
                            resultados_docs = temp_docs
            
            # Si encontramos algo, generar respuesta
            if resultados_rh or resultados_docs:
                return self._responder_con_ia(pregunta, resultados_rh, resultados_docs)
            
            # Si aún no hay resultados, pedir a la IA que responda
            prompt_respuesta = f"""Pregunta del usuario: {pregunta}

No encontré información específica en la base de datos de {len(self.usuarios_rh)} empleados ni en documentos.

Genera una respuesta útil sugiriendo:
1. Reformular la pregunta con más detalles
2. Términos alternativos que podrían funcionar
3. Qué información está disponible

Sé breve y útil."""

            response = self.llm.invoke([HumanMessage(content=prompt_respuesta)])
            return "🤖 " + response.content.strip()
        
        except Exception as e:
            print(f"⚠️ Error en búsqueda inteligente: {e}")
            return self._ayuda()
    
    def _responder_directo(self, resultados_rh: List[Dict], 
                           resultados_docs: List[Dict], pregunta: str) -> str:
        """Respuesta sin IA"""
        if not resultados_rh and not resultados_docs:
            return self._ayuda()
        
        respuesta = ""
        
        if resultados_rh:
            respuesta += f"✅ Encontrados {len(resultados_rh)} empleados:\n\n"
            for u in resultados_rh[:5]:
                respuesta += f"👤 {u.get('nombre_completo')}\n"
                respuesta += f"   💼 {u.get('puesto', {}).get('nombre', 'N/A')}\n"
                respuesta += f"   🏢 {u.get('departamento', {}).get('nombre', 'N/A')}\n"
                respuesta += f"   📧 {u.get('email', 'N/A')}\n\n"
        
        if resultados_docs:
            respuesta += f"✅ Encontrados {len(resultados_docs)} documentos:\n\n"
            for d in resultados_docs[:5]:
                respuesta += f"📄 {d.get('title')}\n"
                respuesta += f"   📅 {d.get('created', 'N/A')}\n\n"
        
        return respuesta
    
    def _ayuda(self) -> str:
        """Mensaje de ayuda"""
        return """❌ No encontré resultados.

💡 Ejemplos de consultas:

📋 Sobre empleados:
  - ¿Cuántos empleados tenemos en Manufactura?
  - Busca a Juan Rodríguez
  - ¿Quién es el jefe de IT?

📄 Sobre documentos:
  - Busca contratos de 2025
  - Encuentra la política de vacaciones
  - ¿Tienes el reporte mensual?

💬 Pregunta general:
  - ¿Quién puede revisar este documento?
  - Busca información sobre el proyecto X"""
    
    def _estadisticas_departamento(self) -> str:
        """Estadísticas por departamento"""
        stats = {}
        for u in self.usuarios_rh:
            depto = u.get('departamento', {}).get('nombre', 'Sin departamento')
            stats[depto] = stats.get(depto, 0) + 1
        
        resultado = "📊 Empleados por Departamento:\n\n"
        for depto, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            resultado += f"   • {depto}: {count}\n"
        
        return resultado
    
    def _estadisticas_area(self) -> str:
        """Estadísticas por área"""
        stats = {}
        for u in self.usuarios_rh:
            area = u.get('area', {}).get('nombre', 'Sin área')
            stats[area] = stats.get(area, 0) + 1
        
        resultado = "📊 Empleados por Área:\n\n"
        for area, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            resultado += f"   • {area}: {count}\n"
        
        return resultado


def main():
    print("🤖 Bot General - Consulta RH y Documentos")
    print("=" * 60)
    print(f"📡 Ollama: {OLLAMA_URL}")
    print(f"📦 Modelo: {OLLAMA_MODEL}")
    print(f"🏢 RH API: {API_RH_URL}")
    if PAPERLESS_URL:
        print(f"📄 Paperless: {PAPERLESS_URL}")
    print()
    
    bot = BotGeneral()
    
    print("\n" + "=" * 60)
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        try:
            pregunta = input("🧑 Pregunta: ").strip()
            
            if not pregunta:
                continue
            
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
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
