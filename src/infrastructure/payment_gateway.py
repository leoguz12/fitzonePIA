from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from ..application.ports import PaymentGateway, ResultadoCobro


class PasarelaSimulada(PaymentGateway):
    """Pasarela de pago simulada para demo y pruebas (sin cargos reales).

    Rechaza cualquier referencia que empiece con ``FAIL`` (ej. ``FAIL-TARJETA``).
    """

    def __init__(self) -> None:
        self.cobros: list[tuple[str, Decimal, str]] = []
        self.reembolsos: list[str] = []

    def cobrar(self, monto: Decimal, referencia_pago: str, concepto: str) -> ResultadoCobro:
        if referencia_pago.strip().upper().startswith("FAIL"):
            return ResultadoCobro(False, None, "Tarjeta rechazada por el banco")
        referencia = f"SIM-{uuid4().hex[:12]}"
        self.cobros.append((referencia, monto, concepto))
        return ResultadoCobro(True, referencia)

    def reembolsar(self, referencia_externa: str) -> None:
        self.reembolsos.append(referencia_externa)
