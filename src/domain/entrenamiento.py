"""Paquete de Entrenamiento Personal (US-13): servicio adicional sujeto a membresía vigente."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import AggregateRoot, nuevo_id
from .errors import AccesoDenegadoError, InvalidData
from .events import PaqueteEntrenamientoContratado
from .membresia import Membresia
from .specifications import ContextoAcceso, acceso_permitido

SERVICIO_ENTRENAMIENTO = "entrenamiento_personal"


def validar_membresia_para_paquete(membresia: Membresia, ahora: datetime) -> None:
    """US-13 E2: con la membresía vencida o suspendida se bloquea la compra."""
    fallas = acceso_permitido().explicar(ContextoAcceso(membresia, ahora.date()))
    if fallas:
        if fallas[0].codigo == "MEMBRESIA_VENCIDA":
            mensaje = "Tu membresía está vencida: renuévala antes de comprar un paquete de entrenamiento personal."
        else:
            mensaje = "Tu membresía está suspendida: regulariza tu situación en recepción antes de comprar."
        raise AccesoDenegadoError(mensaje, [f.codigo for f in fallas])


class PaqueteEntrenamiento(AggregateRoot):
    def __init__(self, id: str, socio_id: str, instructor_id: str, sesiones: int,
                 pago_id: Optional[str], incluido_en_plan: bool, creado_en: datetime) -> None:
        super().__init__()
        if isinstance(sesiones, bool) or not isinstance(sesiones, int) or sesiones <= 0:
            raise InvalidData("El paquete debe tener al menos una sesión")
        self.id, self.socio_id, self.instructor_id = id, socio_id, instructor_id
        self.sesiones, self.pago_id = sesiones, pago_id
        self.incluido_en_plan, self.creado_en = incluido_en_plan, creado_en

    @classmethod
    def contratar(cls, membresia: Membresia, instructor_id: str, sesiones: int,
                  pago_id: Optional[str], ahora: datetime) -> "PaqueteEntrenamiento":
        validar_membresia_para_paquete(membresia, ahora)
        paquete = cls(nuevo_id(), membresia.socio_id, instructor_id, sesiones, pago_id,
                      membresia.plan.incluye(SERVICIO_ENTRENAMIENTO), ahora)
        paquete._registrar(PaqueteEntrenamientoContratado(
            socio_id=membresia.socio_id, instructor_id=instructor_id, sesiones=sesiones, ocurrido_en=ahora))
        return paquete

    @property
    def modulo_agenda_habilitado(self) -> bool:
        """El paquete habilita el módulo para agendar horarios con el instructor elegido."""
        return True
