"""Domain Service: coordina dos agregados (Membresía + ClaseEspecial).

La decisión "¿puede este socio reservar?" involucra a ambos, por eso no vive
en ninguno de los dos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .clase_especial import ClaseEspecial, Reserva
from .errors import AccesoDenegadoError, BusinessRuleViolation, PlanNoIncluyeClaseError
from .membresia import Membresia
from .specifications import ClaseConCupo, ContextoReserva, PlanIncluyeServicio, puede_reservar

_CODIGOS_MEMBRESIA = {"MEMBRESIA_SUSPENDIDA", "MEMBRESIA_VENCIDA"}


@dataclass(frozen=True)
class ResultadoSolicitud:
    tipo: str  # "CONFIRMADA" | "LISTA_ESPERA"
    reserva: Optional[Reserva] = None
    posicion: Optional[int] = None


def validar_elegibilidad(
    clase: ClaseEspecial, membresia: Membresia, socio_id: str, ahora: datetime
) -> ContextoReserva:
    """Aplica la política ``puede_reservar`` y traduce la primera falla a un error."""
    ctx = ContextoReserva(membresia, clase, socio_id, ahora)
    fallas = puede_reservar().explicar(ctx)
    if fallas:
        principal = fallas[0]
        if principal.codigo in _CODIGOS_MEMBRESIA:
            raise AccesoDenegadoError(principal.mensaje, [f.codigo for f in fallas])
        raise BusinessRuleViolation(principal.mensaje, principal.codigo)
    return ctx


def solicitar_lugar(
    clase: ClaseEspecial,
    membresia: Membresia,
    socio_id: str,
    ahora: datetime,
    pago_id: Optional[str] = None,
) -> ResultadoSolicitud:
    ctx = validar_elegibilidad(clase, membresia, socio_id, ahora)
    if pago_id is None and not PlanIncluyeServicio().is_satisfied_by(ctx):
        raise PlanNoIncluyeClaseError(
            "La clase no está incluida en tu plan: requiere un pago adicional.", clase.precio_extra
        )
    if ClaseConCupo().is_satisfied_by(ctx):
        return ResultadoSolicitud("CONFIRMADA", reserva=clase.reservar(socio_id, ahora, pago_id))
    if pago_id is not None:
        raise BusinessRuleViolation("La clase está llena", "CLASE_LLENA")
    return ResultadoSolicitud("LISTA_ESPERA", posicion=clase.unirse_lista_espera(socio_id, ahora))
