from __future__ import annotations

from datetime import date
from typing import Optional

from ..domain.errors import BusinessRuleViolation, NotFound
from ..domain.membresia import Membresia
from ..domain.socio import Socio
from ..domain.value_objects import TipoPlan
from .context import Dependencias
from .pagos import ejecutar_con_cobro
from .ports import UnitOfWork


def socio_o_404(uow: UnitOfWork, socio_id: str) -> Socio:
    socio = uow.socios.get(socio_id)
    if socio is None:
        raise NotFound("El socio no existe")
    return socio


def membresia_o_404(uow: UnitOfWork, socio_id: str) -> Membresia:
    m = uow.membresias.get_por_socio(socio_id)
    if m is None:
        raise NotFound("El socio no tiene membresía")
    return m


class SocioAppService:
    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def registrar(self, nombre: str, email: str) -> Socio:
        socio = Socio.registrar(nombre, email)
        with self.deps.uow_factory() as uow:
            uow.socios.add(socio)
            uow.commit()
        return socio

    def obtener(self, socio_id: str) -> Socio:
        with self.deps.uow_factory() as uow:
            return socio_o_404(uow, socio_id)


class MembresiaAppService:
    """MembresiaAppService.RenovarPlan() / contratar / mejorar / suspender."""

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def _cobrar_y_aplicar(self, socio_id, tipo, referencia_pago, accion, ahora):
        d = self.deps
        with d.uow_factory() as uow:
            socio_o_404(uow, socio_id)
            membresia = ejecutar_con_cobro(
                d, uow, socio_id, d.reglas.tarifas[tipo], f"MEMBRESIA_{tipo.value}",
                referencia_pago, ahora, lambda pago: accion(uow),
            )
        d.bus.publicar(membresia.extraer_eventos())
        return membresia

    def contratar(self, socio_id: str, tipo: TipoPlan, referencia_pago: str, inicio: Optional[date] = None) -> Membresia:
        ahora = self.deps.reloj()

        def accion(uow: UnitOfWork) -> Membresia:
            if uow.membresias.get_por_socio(socio_id) is not None:
                raise BusinessRuleViolation(
                    "El socio ya tiene membresía; usa renovación o mejora de plan", "MEMBRESIA_EXISTENTE"
                )
            m = Membresia.nueva(socio_id, tipo, inicio or ahora.date(), ahora)
            uow.membresias.add(m)
            return m

        return self._cobrar_y_aplicar(socio_id, tipo, referencia_pago, accion, ahora)

    def renovar(self, socio_id: str, tipo: TipoPlan, referencia_pago: str) -> Membresia:
        ahora = self.deps.reloj()

        def accion(uow: UnitOfWork) -> Membresia:
            m = membresia_o_404(uow, socio_id)
            m.renovar(tipo, ahora)
            uow.membresias.save(m)
            return m

        return self._cobrar_y_aplicar(socio_id, tipo, referencia_pago, accion, ahora)

    def mejorar_plan(self, socio_id: str, tipo: TipoPlan, referencia_pago: str) -> Membresia:
        ahora = self.deps.reloj()

        def accion(uow: UnitOfWork) -> Membresia:
            m = membresia_o_404(uow, socio_id)
            m.mejorar_plan(tipo, ahora)
            uow.membresias.save(m)
            return m

        return self._cobrar_y_aplicar(socio_id, tipo, referencia_pago, accion, ahora)

    def suspender(self, socio_id: str, motivo: str) -> Membresia:
        ahora = self.deps.reloj()
        with self.deps.uow_factory() as uow:
            m = membresia_o_404(uow, socio_id)
            m.refrescar_estado(ahora)
            m.suspender(motivo, ahora)
            uow.membresias.save(m)
            uow.commit()
        self.deps.bus.publicar(m.extraer_eventos())
        return m

    def reactivar(self, socio_id: str) -> Membresia:
        ahora = self.deps.reloj()
        with self.deps.uow_factory() as uow:
            m = membresia_o_404(uow, socio_id)
            m.reactivar(ahora)
            uow.membresias.save(m)
            uow.commit()
        self.deps.bus.publicar(m.extraer_eventos())
        return m

    def obtener(self, socio_id: str) -> Membresia:
        with self.deps.uow_factory() as uow:
            m = membresia_o_404(uow, socio_id)
        m.refrescar_estado(self.deps.reloj())  # vista actualizada; no persiste
        return m
