"""Capa conversacional del módulo de consultas.

Detecta mensajes que NO son una consulta de datos (saludos, agradecimientos,
despedidas y peticiones de ayuda) y responde de forma amigable, sin intentar
generar SQL ni llamar a la base de datos. Así el bot no da error ante un "hola"
y puede explicar qué sabe hacer.

Es determinista (sin LLM): rápido y sin coste. Si no reconoce intención
conversacional, devuelve None y el flujo continúa como consulta normal.
"""
import re
import time
import unicodedata
from typing import Dict, List, Optional

from app.core.config import settings
from app.schemas.consultas import ConsultaMeta, ConsultaResponse, TipoSalida
from app.services.consultas import catalogo

# Frases de ayuda/capacidades (se buscan como subcadena en el texto normalizado).
_FRASES_AYUDA = [
    "que puedes hacer", "que puedo hacer", "que puedo preguntar", "que puedo consultar",
    "que sabes hacer", "que haces", "para que sirves", "como funciona", "como te uso",
    "que informacion tienes", "que datos tienes", "opciones", "ayuda", "help", "menu",
    "no se que preguntar", "ejemplos",
]
# Saludos / agradecimientos / despedidas (palabra completa, en mensajes cortos).
_SALUDOS = ["hola", "holi", "buenas", "hey", "saludos", "que tal", "qué tal", "buenos dias",
            "buenas tardes", "buenas noches", "buen dia"]
_GRACIAS = ["gracias", "muchas gracias", "te lo agradezco", "mil gracias"]
_DESPEDIDAS = ["adios", "hasta luego", "nos vemos", "bye", "chao", "hasta pronto"]


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _contiene_palabra(texto: str, terminos: List[str]) -> bool:
    return any(re.search(rf"\b{re.escape(_normalizar(t))}\b", texto) for t in terminos)


def detectar(consulta: str) -> Optional[str]:
    """Clasificar el mensaje como conversacional.

    Devuelve 'ayuda' | 'saludo' | 'agradecimiento' | 'despedida', o None si parece
    una consulta de datos real.
    """
    t = _normalizar(consulta)
    if not t:
        return None

    # Ayuda/capacidades: se reconoce en cualquier longitud.
    if any(frase in t for frase in _FRASES_AYUDA):
        return "ayuda"

    palabras = t.split()
    # Smalltalk: solo en mensajes cortos para no pisar consultas reales.
    if len(palabras) <= 5:
        if _contiene_palabra(t, _GRACIAS):
            return "agradecimiento"
        if _contiene_palabra(t, _DESPEDIDAS):
            return "despedida"
        if _contiene_palabra(t, _SALUDOS):
            return "saludo"
    return None


def _coma_nombre(usuario: Optional[str]) -> str:
    u = (usuario or "").strip()
    return f" {u}" if u else ""


def _capacidades(origen: Dict) -> str:
    """Texto breve con lo que el origen permite consultar (entidades + ejemplos)."""
    entidades = [n for n in catalogo.nombres_items(origen) if n]
    if not entidades:
        return "Aún no hay entidades configuradas en este origen."

    lista = ", ".join(entidades)
    ej = entidades[0]
    ejemplos = [
        f'"¿cuántos {ej} hay?"',
        f'"dame una tabla de {ej}"',
        f'"gráfica de {ej} por categoría"',
    ]
    return (
        f"Puedo consultar (solo lectura): {lista}. "
        f"Por ejemplo: {', '.join(ejemplos)}."
    )


def responder(
    intencion: str,
    origen: Dict,
    origen_clave: str,
    usuario: Optional[str],
    inicio: float,
) -> ConsultaResponse:
    """Construir una respuesta conversacional (tipo=texto) sin tocar la base de datos."""
    nombre = _coma_nombre(usuario)

    bot = settings.APP_NAME

    if intencion == "ayuda":
        titulo = "¿Qué puedo hacer?"
        texto = f"¡Hola{nombre}! Soy {bot}, tu asistente de consultas. {_capacidades(origen)}"
    elif intencion == "agradecimiento":
        titulo = "De nada"
        texto = f"¡Con gusto{nombre}! ¿Quieres hacer otra consulta?"
    elif intencion == "despedida":
        titulo = "Hasta luego"
        texto = f"¡Hasta luego{nombre}! Aquí estaré cuando necesites consultar datos."
    else:  # saludo
        titulo = "Hola"
        texto = (
            f"¡Hola{nombre}! Soy {bot}, tu asistente de consultas de datos. "
            f"{_capacidades(origen)} ¿Qué te gustaría consultar?"
        )

    return ConsultaResponse(
        origen=origen_clave,
        tipo=TipoSalida.texto,
        titulo=titulo,
        texto=texto,
        tabla=None,
        grafico=None,
        meta=ConsultaMeta(
            origen_tipo=origen.get("tipo", "?"),
            consulta_generada=None,
            candidatos=[],
            advertencias=["respuesta conversacional (no se consultó la base de datos)"],
        ),
        tiempo_respuesta=round(time.time() - inicio, 2),
    )
