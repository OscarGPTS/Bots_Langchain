"""Configuración de logging para la aplicación.

Reemplaza los `print()` dispersos. Nunca registrar secretos (tokens, API keys).
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configurar el logging raíz una sola vez."""
    root = logging.getLogger()
    if root.handlers:
        return  # ya configurado (p.ej. por gunicorn)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
