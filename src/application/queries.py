"""CQRS - lado de lectura. No pasan por el modelo de dominio (ADR 0003)."""
from __future__ import annotations

from datetime import date

from ..domain.errors import InvalidData, NotFound
from .context import Dependencias


class ConsultasAppService:
    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def catalogo_clases(self) -> list[dict]:
        """Catálogo general: clases programadas con cupos disponibles (US-05 E2, US-15)."""
        return self.deps.lectura.catalogo(self.deps.reloj())

    def consultar_aforo(self, clase_id: str) -> dict:
        """ConsultarAforoQuery - US-08 / US-15."""
        aforo = self.deps.lectura.aforo(clase_id)
        if aforo is None:
            raise NotFound("La clase no existe")
        return aforo

    def clases_de_instructor(self, instructor_id: str, fecha: date) -> list[dict]:
        return self.deps.lectura.clases_instructor(instructor_id, fecha)

    def reporte_demanda(self, desde: date, hasta: date) -> dict:
        """ReporteDemandaQuery - US-10."""
        if hasta < desde:
            raise InvalidData("El rango de fechas es inválido: 'hasta' es anterior a 'desde'")
        return self.deps.lectura.reporte_demanda(desde, hasta)

    def reservas_del_dia(self, socio_id: str, dia: date) -> list[dict]:
        """US-14: clases reservadas por el socio para hoy (se muestran al validar el ingreso)."""
        return self.deps.lectura.reservas_del_dia(socio_id, dia)

    def notificaciones(self, socio_id: str) -> list[dict]:
        return self.deps.lectura.notificaciones(socio_id)

    def accesos(self, socio_id: str) -> list[dict]:
        return self.deps.lectura.accesos(socio_id)
