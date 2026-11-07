from __future__ import annotations

import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .config import normalizar_url
from .orm import Base


def crear_engine(url: str) -> Engine:
    url = normalizar_url(url)
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool  # una sola conexión para la BD en memoria
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True)


def crear_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)


def crear_tablas(engine: Engine, intentos: int = 10, espera: float = 2.0) -> None:
    """Crea el esquema; reintenta mientras la BD arranca (docker compose / Render)."""
    for intento in range(1, intentos + 1):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError:
            if intento == intentos:
                raise
            time.sleep(espera)
