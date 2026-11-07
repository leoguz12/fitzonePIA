"""Punto de entrada de producción: ``uvicorn src.api.asgi:app``."""
from .main import create_app

app = create_app()
