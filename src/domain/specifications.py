"""Patrón Specification: reglas de negocio como objetos componibles.

Cada regla es una clase pequeña con una sola responsabilidad. Se combinan con
``&`` (AND), ``|`` (OR) y ``~`` (NOT) y pueden *explicar* por qué fallaron,
lo que permite mostrar el motivo en recepción (US-06) y probar cada regla por
separado.

Convención de los mensajes: las reglas que se usan negadas (``~``) describen
la situación prohibida (ej. "La clase está cancelada"); las demás describen lo
que falta ("La membresía no está vigente").
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:  # evita imports circulares
    from .clase_especial import ClaseEspecial
    from .membresia import Membresia

T = TypeVar("T")


@dataclass(frozen=True)
class Falla:
    codigo: str
    mensaje: str


class Specification(ABC, Generic[T]):
    codigo = "ESPECIFICACION"
    mensaje = "No se cumple la regla"

    @abstractmethod
    def is_satisfied_by(self, candidato: T) -> bool: ...

    def explicar(self, candidato: T) -> list[Falla]:
        if self.is_satisfied_by(candidato):
            return []
        return [Falla(self.codigo, self.mensaje)]

    def __and__(self, otra: "Specification[T]") -> "Specification[T]":
        return AndSpecification(self, otra)

    def __or__(self, otra: "Specification[T]") -> "Specification[T]":
        return OrSpecification(self, otra)

    def __invert__(self) -> "Specification[T]":
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    def __init__(self, izquierda: Specification[T], derecha: Specification[T]) -> None:
        self.izquierda, self.derecha = izquierda, derecha

    def is_satisfied_by(self, candidato: T) -> bool:
        return self.izquierda.is_satisfied_by(candidato) and self.derecha.is_satisfied_by(candidato)

    def explicar(self, candidato: T) -> list[Falla]:
        return self.izquierda.explicar(candidato) + self.derecha.explicar(candidato)


class OrSpecification(Specification[T]):
    def __init__(self, izquierda: Specification[T], derecha: Specification[T]) -> None:
        self.izquierda, self.derecha = izquierda, derecha

    def is_satisfied_by(self, candidato: T) -> bool:
        return self.izquierda.is_satisfied_by(candidato) or self.derecha.is_satisfied_by(candidato)

    def explicar(self, candidato: T) -> list[Falla]:
        if self.is_satisfied_by(candidato):
            return []
        return self.izquierda.explicar(candidato) + self.derecha.explicar(candidato)


class NotSpecification(Specification[T]):
    def __init__(self, interna: Specification[T]) -> None:
        self.interna = interna
        self.codigo, self.mensaje = interna.codigo, interna.mensaje

    def is_satisfied_by(self, candidato: T) -> bool:
        return not self.interna.is_satisfied_by(candidato)


# --- Contextos (los candidatos que evalúan las reglas) ---------------------
@dataclass(frozen=True)
class ContextoAcceso:
    membresia: "Membresia"
    dia: date


@dataclass(frozen=True)
class ContextoReserva:
    membresia: "Membresia"
    clase: "ClaseEspecial"
    socio_id: str
    ahora: datetime

    @property
    def dia(self) -> date:
        return self.ahora.date()


@dataclass(frozen=True)
class ContextoCancelacion:
    clase: "ClaseEspecial"
    ahora: datetime
    limite: timedelta


@dataclass(frozen=True)
class ContextoAsistencia:
    clase: "ClaseEspecial"
    ahora: datetime
    tolerancia: timedelta


@dataclass(frozen=True)
class ContextoAutoridad:
    clase: "ClaseEspecial"
    instructor_id: str


# --- Reglas de membresía / acceso -----------------------------------------
class MembresiaVigente(Specification):
    codigo = "MEMBRESIA_VENCIDA"
    mensaje = "La membresía no está vigente (vencida o aún no inicia)."

    def is_satisfied_by(self, c) -> bool:
        return c.membresia.vigencia.vigente_en(c.dia)


class MembresiaNoSuspendida(Specification):
    codigo = "MEMBRESIA_SUSPENDIDA"
    mensaje = "La membresía está suspendida. Pasa a recepción."

    def is_satisfied_by(self, c) -> bool:
        return not c.membresia.suspendida


class PlanIncluyeServicio(Specification):
    codigo = "PLAN_NO_INCLUYE_CLASE"
    mensaje = "La clase no está incluida en el plan contratado."

    def is_satisfied_by(self, c: ContextoReserva) -> bool:
        return c.membresia.plan.incluye(c.clase.servicio_requerido)


# --- Reglas de clase / reserva ---------------------------------------------
class ClaseConCupo(Specification):
    codigo = "CLASE_LLENA"
    mensaje = "La clase alcanzó su capacidad máxima."

    def is_satisfied_by(self, c: ContextoReserva) -> bool:
        return c.clase.cupos_disponibles > 0


class ClaseCancelada(Specification):
    codigo = "CLASE_CANCELADA"
    mensaje = "La clase está cancelada."

    def is_satisfied_by(self, c: ContextoReserva) -> bool:
        return c.clase.cancelada


class ClaseYaIniciada(Specification):
    codigo = "CLASE_YA_INICIADA"
    mensaje = "La clase ya inició; no admite nuevas reservas."

    def is_satisfied_by(self, c: ContextoReserva) -> bool:
        return c.ahora >= c.clase.inicio


class SocioSinLugarEnClase(Specification):
    codigo = "RESERVA_DUPLICADA"
    mensaje = "El socio ya tiene un lugar (o está en lista de espera) en esta clase."

    def is_satisfied_by(self, c: ContextoReserva) -> bool:
        return not c.clase.tiene_lugar(c.socio_id)


class CancelacionATiempo(Specification):
    codigo = "CANCELACION_TARDIA"
    mensaje = "La cancelación se hizo fuera del tiempo permitido."

    def is_satisfied_by(self, c: ContextoCancelacion) -> bool:
        return (c.clase.inicio - c.ahora) >= c.limite


class DentroDeTolerancia(Specification):
    codigo = "FUERA_DE_TOLERANCIA"
    mensaje = "El socio llegó después del tiempo de tolerancia."

    def is_satisfied_by(self, c: ContextoAsistencia) -> bool:
        return c.ahora <= c.clase.inicio + c.tolerancia


class EsInstructorTitular(Specification):
    codigo = "INSTRUCTOR_NO_AUTORIZADO"
    mensaje = "Solo el instructor titular o su suplente puede realizar esta acción."

    def is_satisfied_by(self, c: ContextoAutoridad) -> bool:
        return c.clase.instructor_id == c.instructor_id


class EsInstructorSuplente(Specification):
    codigo = "INSTRUCTOR_NO_AUTORIZADO"
    mensaje = "Solo el instructor titular o su suplente puede realizar esta acción."

    def is_satisfied_by(self, c: ContextoAutoridad) -> bool:
        return c.clase.instructor_suplente_id is not None and (
            c.clase.instructor_suplente_id == c.instructor_id
        )


# --- Políticas compuestas (reglas del BRD combinadas) -----------------------
def acceso_permitido() -> Specification:
    """CU-01 / US-01 / US-06: membresía no suspendida Y vigente."""
    return MembresiaNoSuspendida() & MembresiaVigente()


def puede_reservar() -> Specification:
    """CU-02 / US-02: socio con acceso, clase disponible y sin lugar previo."""
    return (
        MembresiaNoSuspendida()
        & MembresiaVigente()
        & ~ClaseCancelada()
        & ~ClaseYaIniciada()
        & SocioSinLugarEnClase()
    )


def puede_gestionar_sesion() -> Specification:
    """US-09: titular O suplente."""
    return EsInstructorTitular() | EsInstructorSuplente()
