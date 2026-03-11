"""
Script para probar la API de Recursos Humanos
==============================================
Este script hace una prueba rápida de conexión con la API
y muestra estadísticas básicas.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_URL = os.getenv('API_RH_URL')

def probar_api():
    """
    Prueba la conexión con la API de RH
    """
    if not API_URL:
        print("❌ Error: API_RH_URL no está configurado en el archivo .env")
        return
    
    print("🔍 Probando conexión con la API de Recursos Humanos...")
    print(f"📡 URL: {API_URL}/users\n")
    
    try:
        # Hacer petición GET
        response = requests.get(f"{API_URL}/users", timeout=15)
        
        # Verificar status code
        if response.status_code != 200:
            print(f"❌ Error: Status code {response.status_code}")
            return
        
        print(f"✅ Conexión exitosa (Status: {response.status_code})\n")
        
        # Parsear JSON
        data = response.json()
        
        if not data.get('success'):
            print("❌ La API respondió pero con success=false")
            return
        
        usuarios = data.get('data', [])
        total = data.get('total', 0)
        
        print("=" * 60)
        print("📊 ESTADÍSTICAS DE LA API")
        print("=" * 60)
        print(f"\n✅ Total de usuarios: {total}")
        print(f"✅ Usuarios obtenidos: {len(usuarios)}\n")
        
        # Estadísticas por departamento
        departamentos = {}
        areas = {}
        puestos = {}
        activos = 0
        
        for usuario in usuarios:
            # Contar departamentos
            dept = usuario.get('departamento', {})
            if dept:
                dept_nombre = dept.get('nombre', 'Sin departamento')
                departamentos[dept_nombre] = departamentos.get(dept_nombre, 0) + 1
            
            # Contar áreas
            area = usuario.get('area', {})
            if area:
                area_nombre = area.get('nombre', 'Sin área')
                areas[area_nombre] = areas.get(area_nombre, 0) + 1
            
            # Contar puestos
            puesto = usuario.get('puesto', {})
            if puesto:
                puesto_nombre = puesto.get('nombre', 'Sin puesto')
                puestos[puesto_nombre] = puestos.get(puesto_nombre, 0) + 1
            
            # Contar activos
            if usuario.get('activo', False):
                activos += 1
        
        print(f"👥 Empleados activos: {activos}")
        print(f"💤 Empleados inactivos: {len(usuarios) - activos}\n")
        
        # Mostrar departamentos
        print("🏢 DEPARTAMENTOS:")
        for dept, count in sorted(departamentos.items(), key=lambda x: x[1], reverse=True):
            porcentaje = (count / len(usuarios)) * 100
            print(f"   • {dept}: {count} ({porcentaje:.1f}%)")
        
        print(f"\n📊 ÁREAS (Top 5):")
        top_areas = sorted(areas.items(), key=lambda x: x[1], reverse=True)[:5]
        for area, count in top_areas:
            porcentaje = (count / len(usuarios)) * 100
            print(f"   • {area}: {count} ({porcentaje:.1f}%)")
        
        print(f"\n💼 PUESTOS (Top 5):")
        top_puestos = sorted(puestos.items(), key=lambda x: x[1], reverse=True)[:5]
        for puesto, count in top_puestos:
            print(f"   • {puesto}: {count}")
        
        # Mostrar ejemplo de un usuario
        print("\n" + "=" * 60)
        print("👤 EJEMPLO DE USUARIO:")
        print("=" * 60)
        
        if usuarios:
            usuario = usuarios[0]
            print(f"\nNombre: {usuario.get('nombre_completo')}")
            print(f"Email: {usuario.get('email', 'N/A')}")
            print(f"Teléfono: {usuario.get('telefono', 'N/A')}")
            print(f"Puesto: {usuario.get('puesto', {}).get('nombre', 'N/A')}")
            print(f"Departamento: {usuario.get('departamento', {}).get('nombre', 'N/A')}")
            print(f"Área: {usuario.get('area', {}).get('nombre', 'N/A')}")
            
            jefe = usuario.get('jefe_directo', {})
            if jefe:
                print(f"Jefe Directo: {jefe.get('nombre_completo', 'N/A')}")
                print(f"Email Jefe: {jefe.get('email', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ PRUEBA EXITOSA - La API está funcionando correctamente")
        print("=" * 60)
        print("\n💡 Ahora puedes ejecutar:")
        print("   python bot_empresa_rh.py")
        print("   python bot_empresa_combinado.py\n")
        
    except requests.exceptions.Timeout:
        print("❌ Error: Timeout - La API no respondió a tiempo")
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar a la API")
        print("💡 Verifica tu conexión a internet/red")
    except json.JSONDecodeError:
        print("❌ Error: La respuesta no es JSON válido")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    probar_api()
