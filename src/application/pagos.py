"""Cobro con compensación.

Un rollback de base de datos NO deshace un cobro bancario. Si el cobro se
aprobó pero la operación de negocio falla (ej. otro socio tomó el último
lugar), se reembolsa y se deja constancia del pago como REEMBOLSADO.
Esto responde al riesgo "cobrar sin registrar la reserva" del reporte U5.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable, TypeVar

from ..domain.errors import PagoRechazadoError
from ..domain.pago import Pago
from .context import Dependencias
from .ports import UnitOfWork

R = TypeVar("R")


def ejecutar_con_cobro(
    deps: Dependencias,
    uow: UnitOfWork,
    socio_id: str,
    monto: Decimal,
    concepto: str,
    referencia_pago: str,
    ahora: datetime,
    operacion: Callable[[Pago], R],
) -> R:
    cobro = deps.pasarela.cobrar(monto, referencia_pago, concepto)
    pago = Pago.registrar(socio_id, monto, concepto, cobro.aprobado, cobro.referencia_externa, ahora)
    if not pago.aprobado:
        uow.pagos.add(pago)  # queda constancia del intento rechazado
        uow.commit()
        raise PagoRechazadoError(cobro.motivo or "El pago fue rechazado")
    uow.pagos.add(pago)
    try:
        resultado = operacion(pago)
        uow.commit()
        return resultado
    except Exception:
        uow.rollback()
        deps.pasarela.reembolsar(cobro.referencia_externa or "")
        pago.reembolsar()
        uow.pagos.add(pago)
        uow.commit()
        raise
