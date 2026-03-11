"""Bot de Recursos Humanos - Con IA"""
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
OLLAMA_URL = os.getenv('OLLAMA_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi4-mini:latest')


class BotRH:
    """Bot especializado en consultas de Recursos Humanos"""
    
    def __init__(self):
        self.usuarios = []
        self.llm = None
        self._inicializar_ia()
        self._cargar_usuarios()
    
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
    
    def _cargar_usuarios(self):
        """Cargar usuarios desde la API"""
        try:
            response = requests.get(f"{API_RH_URL}/users", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.usuarios = data.get('data', [])
            print(f"✅ {len(self.usuarios)} empleados cargados\n")
        except Exception as e:
            print(f"❌ Error al cargar empleados: {e}\n")
    
    def buscar(self, termino: str) -> List[Dict]:
        """Buscar empleados por nombre, departamento o área"""
        termino = termino.lower()
        resultados = []
        
        for usuario in self.usuarios:
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
        
        return resultados
    
    def procesar(self, pregunta: str) -> str:
        """Procesar pregunta del usuario"""
        pregunta_lower = pregunta.lower()
        
        # Estadísticas
        if 'cuántos' in pregunta_lower or 'total' in pregunta_lower:
            if 'departamento' in pregunta_lower:
                return self._estadisticas_departamento()
            elif 'área' in pregunta_lower or 'area' in pregunta_lower:
                return self._estadisticas_area()
            else:
                activos = sum(1 for u in self.usuarios if u.get('activo', False))
                return f"📊 Total: {len(self.usuarios)} empleados ({activos} activos)"
        
        # Buscar empleados
        resultados = []
        palabras = pregunta.split()
        for palabra in palabras:
            if len(palabra) > 3:
                temp = self.buscar(palabra.strip('¿?.,'))
                if temp:
                    resultados = temp
                    break
        
        if resultados:
            return self._responder_con_ia(pregunta, resultados)
        
        return self._ayuda()
    
    def _responder_con_ia(self, pregunta: str, resultados: List[Dict]) -> str:
        """Generar respuesta usando IA"""
        if not self.llm:
            return self._formatear_resultados(resultados)
        
        try:
            # Preparar datos para la IA
            datos = []
            for u in resultados[:5]:
                datos.append({
                    'nombre': u.get('nombre_completo'),
                    'puesto': u.get('puesto', {}).get('nombre'),
                    'departamento': u.get('departamento', {}).get('nombre'),
                    'area': u.get('area', {}).get('nombre'),
                    'email': u.get('email'),
                    'telefono': u.get('telefono'),
                    'jefe': u.get('jefe_directo', {}).get('nombre_completo')
                })
            
            prompt = f"""Pregunta: {pregunta}

Empleados encontrados:
{json.dumps(datos, ensure_ascii=False, indent=2)}

Responde de forma directa. Si hay un solo empleado, muestra su información.
Si hay varios, lista los nombres y pregunta cuál le interesa."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            respuesta = response.content.strip()
            
            # Agregar detalles formateados
            resultado = respuesta + "\n\n" + self._formatear_resultados(resultados, max_items=5)
            return resultado
        
        except Exception as e:
            print(f"⚠️ Error de IA: {e}")
            return self._formatear_resultados(resultados)
    
    def _formatear_resultados(self, resultados: List[Dict], max_items: int = 10) -> str:
        """Formatear lista de resultados"""
        if not resultados:
            return "❌ No se encontraron resultados"
        
        texto = f"{'─'*50}\n"
        for u in resultados[:max_items]:
            texto += f"👤 {u.get('nombre_completo')}\n"
            texto += f"   📧 {u.get('email', 'N/A')}\n"
            if u.get('telefono'):
                texto += f"   📱 {u.get('telefono')}\n"
            texto += f"   💼 {u.get('puesto', {}).get('nombre', 'N/A')}\n"
            texto += f"   🏢 {u.get('departamento', {}).get('nombre', 'N/A')}\n"
            texto += f"   📊 {u.get('area', {}).get('nombre', 'N/A')}\n"
            
            jefe = u.get('jefe_directo', {})
            if jefe and jefe.get('nombre_completo'):
                texto += f"   👔 Jefe: {jefe.get('nombre_completo')}\n"
            
            texto += "\n"
        
        if len(resultados) > max_items:
            texto += f"... y {len(resultados) - max_items} más.\n"
        
        return texto
    
    def _estadisticas_departamento(self) -> str:
        """Estadísticas por departamento"""
        stats = {}
        for u in self.usuarios:
            depto = u.get('departamento', {}).get('nombre', 'Sin departamento')
            stats[depto] = stats.get(depto, 0) + 1
        
        resultado = "📊 Empleados por Departamento:\n\n"
        for depto, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            resultado += f"   • {depto}: {count}\n"
        
        return resultado
    
    def _estadisticas_area(self) -> str:
        """Estadísticas por área"""
        stats = {}
        for u in self.usuarios:
            area = u.get('area', {}).get('nombre', 'Sin área')
            stats[area] = stats.get(area, 0) + 1
        
        resultado = "📊 Empleados por Área:\n\n"
        for area, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            resultado += f"   • {area}: {count}\n"
        
        return resultado
    
    def _ayuda(self) -> str:
        """Mensaje de ayuda"""
        return """❌ No encontré resultados.

💡 Ejemplos de consultas:
  - ¿Cuántos empleados tenemos?
  - Busca a Juan Rodríguez
  - Lista del departamento de Manufactura
  - ¿Quién es el jefe de IT?
  - Empleados del área de Servicios Técnicos"""


def main():
    print("🤖 Bot de Recursos Humanos")
    print("=" * 60)
    print(f"📡 Ollama: {OLLAMA_URL}")
    print(f"📦 Modelo: {OLLAMA_MODEL}\n")
    
    bot = BotRH()
    
    if not bot.usuarios:
        print("❌ No se pudieron cargar los empleados. Verifica la conexión.")
        return
    
    print("=" * 60)
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
