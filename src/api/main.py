from __future__ import annotations

from typing import Optional

from fastapi import FastAPI

from ..application.ports import Clock, PaymentGateway
from ..infrastructure.config import Settings
from ..infrastructure.db import crear_tablas
from ..infrastructure.seed import sembrar_datos_demo
from .container import Container, build_container
from .errors import registrar_manejadores
from .routers import accesos, clases, instructores, reportes, socios

DESCRIPCION = """
API REST de **FitZone**: membresías, control de acceso, reservas de clases especiales,
lista de espera automática, No-Shows y reportes de demanda.

Códigos de error: `402` requiere pago adicional · `403` acceso denegado · `404` no existe ·
`409` regla de negocio / transición inválida · `422` datos inválidos.
"""


def create_app(
    settings: Optional[Settings] = None,
    container: Optional[Container] = None,
    reloj: Optional[Clock] = None,
    pasarela: Optional[PaymentGateway] = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    container = container or build_container(settings, reloj=reloj, pasarela=pasarela)
    crear_tablas(container.engine)
    if settings.seed_demo_data:
        sembrar_datos_demo(container.deps, container.session_factory)

    app = FastAPI(title="FitZone API", version="1.0.0", description=DESCRIPCION)
    app.state.container = container
    registrar_manejadores(app)
    for router in (socios.router, accesos.router, instructores.router, clases.router, reportes.router):
        app.include_router(router)

    @app.get("/health", tags=["Sistema"], summary="Estado del servicio")
    def health() -> dict:
        return {"status": "ok", "entorno": settings.app_env,
                "hora_servidor": container.deps.reloj().isoformat(timespec="seconds")}

    return app
