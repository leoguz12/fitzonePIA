from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .event_bus import EventBus
from .ports import Clock, PaymentGateway, ReadModel, UnitOfWork
from .reglas import ReglasNegocio


@dataclass
class Dependencias:
    """Todo lo que necesitan los servicios, inyectado (Dependency Inversion)."""

    uow_factory: Callable[[], UnitOfWork]
    reloj: Clock
    pasarela: PaymentGateway
    bus: EventBus
    reglas: ReglasNegocio
    lectura: ReadModel
