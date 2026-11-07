"""Value Objects: inmutables, sin identidad, definidos por sus atributos."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from enum import Enum

from .errors import InvalidData


def add_months(d: date, meses: int) -> date:
    """Suma meses de calendario conservando el día (ajusta a fin de mes)."""
    total = d.month - 1 + meses
    anio = d.year + total // 12
    mes = total % 12 + 1
    dia = min(d.day, calendar.monthrange(anio, mes)[1])
    return date(anio, mes, dia)


def fin_de_mes(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


class TipoPlan(str, Enum):
    MENSUAL = "MENSUAL"
    TRIMESTRAL = "TRIMESTRAL"
    ANUAL = "ANUAL"

    @property
    def meses(self) -> int:
        return {"MENSUAL": 1, "TRIMESTRAL": 3, "ANUAL": 12}[self.value]

    @property
    def nivel(self) -> int:
        return {"MENSUAL": 1, "TRIMESTRAL": 2, "ANUAL": 3}[self.value]


# Catálogo de servicios por plan. Agregar un plan nuevo = agregar una entrada
# (Open/Closed): ningún servicio de aplicación necesita cambiar.
SERVICIOS_POR_PLAN: dict[TipoPlan, frozenset[str]] = {
    TipoPlan.MENSUAL: frozenset({"funcional"}),
    TipoPlan.TRIMESTRAL: frozenset({"funcional", "yoga", "spinning"}),
    TipoPlan.ANUAL: frozenset(
        {"funcional", "yoga", "spinning", "crossfit", "entrenamiento_personal"}
    ),
}


@dataclass(frozen=True)
class Vigencia:
    fecha_inicio: date
    fecha_vencimiento: date

    def __post_init__(self) -> None:
        if self.fecha_vencimiento <= self.fecha_inicio:
            raise InvalidData("La fecha de vencimiento debe ser posterior a la de inicio")

    @classmethod
    def desde(cls, inicio: date, tipo: TipoPlan) -> "Vigencia":
        return cls(inicio, add_months(inicio, tipo.meses))

    def vigente_en(self, dia: date) -> bool:
        """El último día (fecha de vencimiento) todavía es válido."""
        return self.fecha_inicio <= dia <= self.fecha_vencimiento

    def vencida_en(self, dia: date) -> bool:
        return dia > self.fecha_vencimiento


@dataclass(frozen=True)
class PlanContratado:
    tipo: TipoPlan
    servicios_incluidos: frozenset[str]

    @classmethod
    def de_tipo(cls, tipo: TipoPlan) -> "PlanContratado":
        return cls(tipo, SERVICIOS_POR_PLAN[tipo])

    def incluye(self, servicio: str) -> bool:
        return servicio.strip().lower() in self.servicios_incluidos


@dataclass(frozen=True)
class CapacidadMaxima:
    limite: int

    def __post_init__(self) -> None:
        if isinstance(self.limite, bool) or not isinstance(self.limite, int) or self.limite <= 0:
            raise InvalidData("La capacidad máxima debe ser un entero mayor a cero")
