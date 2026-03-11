"""Test de casos reales de uso"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.bot_documentos import BotDocumentos

bot = BotDocumentos()

casos = [
    # Caso 1: Query específica con sección
    ("codigo de etica punto 4.19", "Buscar sección específica de documento"),
    
    # Caso 2: Query específica con parte del título
    ("usuarios activos de GPT", "Buscar con términos específicos"),
    
    # Caso 3: Pregunta sobre contenido
    ("¿Qué dice sobre integridad?", "Pregunta directa sobre tema"),
    
    # Caso 4: Búsqueda simple
    ("codigo", "Búsqueda de una palabra"),
    
    # Caso 5: Comando especial
    ("lista documentos recientes", "Listar documentos"),
]

for i, (consulta, descripcion) in enumerate(casos, 1):
    print(f"\n{'='*70}")
    print(f"Caso {i}: {descripcion}")
    print(f"Consulta: {consulta}")
    print('='*70)
    resultado = bot.procesar(consulta)
    
    # Mostrar resumen del resultado
    lineas = resultado.split('\n')
    if len(resultado) > 300:
        print('\n'.join(lineas[:10]))
        print(f"... ({len(lineas)-10} líneas más)")
    else:
        print(resultado)
