"""
Script para Generar Token de API de Paperless
==============================================
Si no tienes un token de API, este script te muestra cómo obtenerlo.
"""

import requests

print("=" * 70)
print("🔑 CÓMO OBTENER TOKEN DE API DE PAPERLESS")
print("=" * 70)
print()
print("Hay 2 formas de obtener un token:")
print()
print("=" * 70)
print("📱 FORMA 1: Desde la Interfaz Web (Recomendada)")
print("=" * 70)
print()
print("1. Entra a tu Paperless en el navegador")
print("   Ejemplo: https://paperless.tech-energy.lat")
print()
print("2. Inicia sesión con tu usuario y contraseña")
print()
print("3. Ve a Settings → API Tokens")
print("   O busca en el menú: 'Auth Tokens' o 'API'")
print()
print("4. Click en 'Create Token' o 'Nuevo Token'")
print()
print("5. Copia el token generado")
print()
print("6. Pégalo en config_apis.py línea 10:")
print('   PAPERLESS_TOKEN = "tu_token_copiado_aqui"')
print()
print("=" * 70)
print("🔧 FORMA 2: Desde la API (Si tienes usuario/contraseña)")
print("=" * 70)
print()

url = input("📡 URL de tu Paperless (ej: https://paperless.ejemplo.com): ").strip()
if not url:
    print("\n⚠️ No ingresaste URL. Usa la Forma 1 (interfaz web)")
    exit()

username = input("👤 Tu usuario de Paperless: ").strip()
password = input("🔐 Tu contraseña: ").strip()

if not username or not password:
    print("\n⚠️ Faltan datos. Usa la Forma 1 (interfaz web)")
    exit()

print("\n🔄 Intentando obtener token...")

try:
    # Paperless usa un endpoint de token
    response = requests.post(
        f"{url}/api/token/",
        json={"username": username, "password": password},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        
        if token:
            print("\n✅ ¡Token obtenido exitosamente!")
            print("=" * 70)
            print(f"🔑 TOKEN: {token}")
            print("=" * 70)
            print()
            print("📝 Copia este token y pégalo en config_apis.py:")
            print(f'PAPERLESS_TOKEN = "{token}"')
            print()
        else:
            print("\n❌ No se recibió token en la respuesta")
            print("💡 Usa la Forma 1 (interfaz web)")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
        print("💡 Verifica usuario/contraseña o usa la Forma 1 (interfaz web)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("💡 Usa la Forma 1 (interfaz web) - es más fácil")

print()
print("=" * 70)
print("📚 SIGUIENTE PASO:")
print("=" * 70)
print()
print("1. Edita config_apis.py")
print("2. Pega tu URL y TOKEN")
print("3. Ejecuta: python probar_paperless.py")
print()
