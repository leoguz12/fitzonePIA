"""Excepciones del dominio FitZone.

Cada excepción tiene un ``codigo`` estable que la capa API traduce a un
código HTTP (404, 409, 422...). El dominio no conoce HTTP.
"""
from __future__ import annotations

from decimal import Decimal


class DomainError(Exception):
    codigo = "ERROR_DE_DOMINIO"

    def __init__(self, mensaje: str, codigo: str | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo


class InvalidData(DomainError):
    """Datos que violan un invariante (ej. capacidad negativa)."""

    codigo = "DATOS_INVALIDOS"


class InvalidTransition(DomainError):
    """Transición no permitida por una máquina de estados."""

    codigo = "TRANSICION_INVALIDA"


class BusinessRuleViolation(DomainError):
    """Regla de negocio incumplida (clase llena, reserva duplicada...)."""

    codigo = "REGLA_DE_NEGOCIO"


class NotFound(DomainError):
    codigo = "NO_ENCONTRADO"


class Forbidden(DomainError):
    codigo = "PROHIBIDO"


class AccesoDenegadoError(DomainError):
    """Membresía vencida o suspendida: se niega acceso o reserva."""

    codigo = "ACCESO_DENEGADO"

    def __init__(self, mensaje: str, codigos: list[str] | None = None) -> None:
        super().__init__(mensaje)
        self.codigos = codigos or []


class PlanNoIncluyeClaseError(DomainError):
    """La clase no está en el plan del socio: requiere pago adicional."""

    codigo = "REQUIERE_PAGO_ADICIONAL"

    def __init__(self, mensaje: str, monto: Decimal) -> None:
        super().__init__(mensaje)
        self.monto = monto


class PagoRechazadoError(DomainError):
    codigo = "PAGO_RECHAZADO"
