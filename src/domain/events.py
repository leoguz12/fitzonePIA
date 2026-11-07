"""Eventos de dominio (lenguaje ubicuo de FitZone).

Un evento describe algo que YA ocurrió; por eso se registra solo después de
una transición válida.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    ocurrido_en: datetime


# --- Clase especial / reservas -------------------------------------------
@dataclass(frozen=True, kw_only=True)
class ReservaConfirmada(DomainEvent):
    clase_id: str
    socio_id: str
    reserva_id: str


@dataclass(frozen=True, kw_only=True)
class CapacidadAlcanzada(DomainEvent):
    clase_id: str


@dataclass(frozen=True, kw_only=True)
class SocioAgregadoAListaEspera(DomainEvent):
    clase_id: str
    socio_id: str
    posicion: int


@dataclass(frozen=True, kw_only=True)
class LugarLiberado(DomainEvent):
    clase_id: str
    reserva_id: str
    socio_id: str


@dataclass(frozen=True, kw_only=True)
class SocioAsignadoDesdeEspera(DomainEvent):
    clase_id: str
    socio_id: str
    reserva_id: str


@dataclass(frozen=True, kw_only=True)
class AsistenciaRegistrada(DomainEvent):
    clase_id: str
    socio_id: str


@dataclass(frozen=True, kw_only=True)
class NoShowRegistrado(DomainEvent):
    clase_id: str
    socio_id: str
    reserva_id: str


@dataclass(frozen=True, kw_only=True)
class CancelacionTardiaRegistrada(DomainEvent):
    clase_id: str
    socio_id: str


@dataclass(frozen=True, kw_only=True)
class ClaseCancelada(DomainEvent):
    clase_id: str
    socios_afectados: tuple[str, ...]
    motivo: str


@dataclass(frozen=True, kw_only=True)
class InstructorSuplenteAsignado(DomainEvent):
    clase_id: str
    instructor_id: str
    socios_afectados: tuple[str, ...]


# --- Membresía / acceso ----------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class AccesoPermitido(DomainEvent):
    socio_id: str
    advertencia: str | None = None


@dataclass(frozen=True, kw_only=True)
class AccesoDenegado(DomainEvent):
    socio_id: str
    motivo: str


@dataclass(frozen=True, kw_only=True)
class MembresiaContratada(DomainEvent):
    socio_id: str
    tipo: str
    vencimiento: date


@dataclass(frozen=True, kw_only=True)
class MembresiaRenovada(DomainEvent):
    socio_id: str
    tipo: str
    vencimiento: date


@dataclass(frozen=True, kw_only=True)
class MembresiaMejorada(DomainEvent):
    socio_id: str
    tipo: str
    vencimiento: date


@dataclass(frozen=True, kw_only=True)
class PaqueteEntrenamientoContratado(DomainEvent):
    socio_id: str
    instructor_id: str
    sesiones: int


@dataclass(frozen=True, kw_only=True)
class MembresiaSuspendida(DomainEvent):
    socio_id: str
    motivo: str


@dataclass(frozen=True, kw_only=True)
class MembresiaReactivada(DomainEvent):
    socio_id: str
