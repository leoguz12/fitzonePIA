"""Puertos de la capa de aplicación (interfaces que implementa infraestructura)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Optional

from ..domain.repositories import (
    ClaseRepository, EntrenamientoRepository, InstructorRepository, MembresiaRepository, PagoRepository,
    SocioRepository,
)

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class RegistroAcceso:
    socio_id: str
    permitido: bool
    motivo: Optional[str]
    advertencia: Optional[str]
    ocurrido_en: datetime


@dataclass(frozen=True)
class Notificacion:
    socio_id: str
    asunto: str
    mensaje: str
    creada_en: datetime


class AccesoRepository(ABC):
    @abstractmethod
    def add(self, registro: RegistroAcceso) -> None: ...


class NotificacionRepository(ABC):
    @abstractmethod
    def add(self, notificacion: Notificacion) -> None: ...


class UnitOfWork(ABC):
    """Una transacción = una unidad de trabajo (ACID). Ver ADR 0002."""

    socios: SocioRepository
    membresias: MembresiaRepository
    instructores: InstructorRepository
    clases: ClaseRepository
    pagos: PagoRepository
    entrenamientos: EntrenamientoRepository
    accesos: AccesoRepository
    notificaciones: NotificacionRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> bool: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


@dataclass(frozen=True)
class ResultadoCobro:
    aprobado: bool
    referencia_externa: Optional[str]
    motivo: Optional[str] = None


class PaymentGateway(ABC):
    @abstractmethod
    def cobrar(self, monto: Decimal, referencia_pago: str, concepto: str) -> ResultadoCobro: ...

    @abstractmethod
    def reembolsar(self, referencia_externa: str) -> None: ...


class ReadModel(ABC):
    """Lado de lectura de CQRS: SQL directo que devuelve DTOs planos (ADR 0003)."""

    @abstractmethod
    def catalogo(self, ahora: datetime) -> list[dict[str, Any]]: ...

    @abstractmethod
    def aforo(self, clase_id: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    def clases_instructor(self, instructor_id: str, fecha: date) -> list[dict[str, Any]]: ...

    @abstractmethod
    def reporte_demanda(self, desde: date, hasta: date) -> dict[str, Any]: ...

    @abstractmethod
    def reservas_del_dia(self, socio_id: str, dia: date) -> list[dict[str, Any]]: ...

    @abstractmethod
    def notificaciones(self, socio_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def accesos(self, socio_id: str) -> list[dict[str, Any]]: ...
