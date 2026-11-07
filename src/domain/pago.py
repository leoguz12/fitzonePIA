from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base import AggregateRoot, nuevo_id
from .errors import InvalidData
from .state_machine import StateMachine


class EstadoPago(str, Enum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    REEMBOLSADO = "REEMBOLSADO"


PAGO_FSM: StateMachine[EstadoPago] = StateMachine(
    "Pago", {(EstadoPago.APROBADO, "reembolsar"): EstadoPago.REEMBOLSADO}
)


class Pago(AggregateRoot):
    def __init__(
        self,
        id: str,
        socio_id: str,
        monto: Decimal,
        concepto: str,
        estado: EstadoPago,
        referencia_externa: str | None,
        creado_en: datetime,
    ) -> None:
        super().__init__()
        if monto is None or Decimal(monto) <= 0:
            raise InvalidData("El monto del pago debe ser mayor a cero")
        if not concepto or not concepto.strip():
            raise InvalidData("El pago requiere un concepto")
        self.id = id
        self.socio_id = socio_id
        self.monto = Decimal(monto)
        self.concepto = concepto
        self.estado = estado
        self.referencia_externa = referencia_externa
        self.creado_en = creado_en

    @classmethod
    def registrar(
        cls,
        socio_id: str,
        monto: Decimal,
        concepto: str,
        aprobado: bool,
        referencia_externa: str | None,
        ahora: datetime,
    ) -> "Pago":
        estado = EstadoPago.APROBADO if aprobado else EstadoPago.RECHAZADO
        return cls(nuevo_id(), socio_id, monto, concepto, estado, referencia_externa, ahora)

    @property
    def aprobado(self) -> bool:
        return self.estado == EstadoPago.APROBADO

    def reembolsar(self) -> None:
        self.estado = PAGO_FSM.disparar(self.estado, "reembolsar")
