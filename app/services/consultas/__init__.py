"""Módulo de Consultas a Datos: NL -> SQL (MySQL read-only) / NL -> API REST.

Reutiliza el LLM configurado del proyecto (LLM_PROVIDER) y un catálogo de reglas
(`config/rules.yaml`) que acota qué tablas/recursos puede consultar el bot.
El sistema es estrictamente de SOLO LECTURA.
"""
