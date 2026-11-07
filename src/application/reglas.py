from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Mapping

from ..domain.value_objects import TipoPlan


@dataclass(frozen=True)
class ReglasNegocio:
    """Parámetros de negocio configurables (12-Factor: vienen del entorno).

    Los valores por defecto son SUPUESTOS documentados en el BRD (preguntas
    P2, P5 y P6 pendientes de confirmar con el stakeholder).
    """

    tolerancia: timedelta = timedelta(minutes=10)
    limite_cancelacion: timedelta = timedelta(hours=2)
    tarifa_sesion_entrenamiento: Decimal = Decimal("300.00")
    tarifas: Mapping[TipoPlan, Decimal] = field(
        default_factory=lambda: {
            TipoPlan.MENSUAL: Decimal("600.00"),
            TipoPlan.TRIMESTRAL: Decimal("1500.00"),
            TipoPlan.ANUAL: Decimal("5000.00"),
        }
    )
