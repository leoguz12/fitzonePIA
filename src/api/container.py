"""Composition root: aquí (y solo aquí) se conectan las implementaciones concretas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..application.acceso_service import AccesoAppService
from ..application.asistencia_service import AsistenciaAppService
from ..application.clase_service import ClaseAppService
from ..application.context import Dependencias
from ..application.entrenamiento_service import EntrenamientoAppService
from ..application.event_bus import EventBus
from ..application.handlers import registrar_handlers
from ..application.lista_espera_service import ListaEsperaAppService
from ..application.membresia_service import MembresiaAppService, SocioAppService
from ..application.ports import Clock, PaymentGateway
from ..application.queries import ConsultasAppService
from ..application.reserva_service import ReservaAppService
from ..infrastructure.config import Settings
from ..infrastructure.db import crear_engine, crear_session_factory
from ..infrastructure.payment_gateway import PasarelaSimulada
from ..infrastructure.read_model import SqlReadModel
from ..infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class Container:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker
    deps: Dependencias
    socios: SocioAppService
    membresias: MembresiaAppService
    accesos: AccesoAppService
    reservas: ReservaAppService
    lista_espera: ListaEsperaAppService
    asistencia: AsistenciaAppService
    clases: ClaseAppService
    consultas: ConsultasAppService
    entrenamiento: EntrenamientoAppService


def build_container(
    settings: Settings,
    reloj: Optional[Clock] = None,
    pasarela: Optional[PaymentGateway] = None,
) -> Container:
    engine = crear_engine(settings.database_url)
    session_factory = crear_session_factory(engine)
    deps = Dependencias(
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        reloj=reloj or datetime.now,  # hora local del servidor (naive)
        pasarela=pasarela or PasarelaSimulada(),
        bus=EventBus(),
        reglas=settings.reglas(),
        lectura=SqlReadModel(session_factory),
    )
    registrar_handlers(deps)
    return Container(
        settings, engine, session_factory, deps,
        socios=SocioAppService(deps), membresias=MembresiaAppService(deps), accesos=AccesoAppService(deps),
        reservas=ReservaAppService(deps), lista_espera=ListaEsperaAppService(deps),
        asistencia=AsistenciaAppService(deps), clases=ClaseAppService(deps), consultas=ConsultasAppService(deps),
        entrenamiento=EntrenamientoAppService(deps),
    )
