from __future__ import annotations

from ..domain.clase_especial import ClaseEspecial
from ..domain.errors import AccesoDenegadoError, BusinessRuleViolation, NotFound
from ..domain.membresia import Membresia
from ..domain.services import ResultadoSolicitud, solicitar_lugar, validar_elegibilidad
from ..domain.specifications import ClaseConCupo, PlanIncluyeServicio
from .context import Dependencias
from .membresia_service import socio_o_404
from .pagos import ejecutar_con_cobro
from .ports import UnitOfWork


def clase_o_404(uow: UnitOfWork, clase_id: str, bloquear: bool = False) -> ClaseEspecial:
    clase = uow.clases.get(clase_id, bloquear=bloquear)
    if clase is None:
        raise NotFound("La clase no existe")
    return clase


def _membresia_vigente(uow: UnitOfWork, socio_id: str, ahora) -> Membresia:
    socio_o_404(uow, socio_id)
    m = uow.membresias.get_por_socio(socio_id)
    if m is None:
        raise AccesoDenegadoError("El socio no tiene una membresía contratada", ["SIN_MEMBRESIA"])
    m.refrescar_estado(ahora)
    return m


class ReservaAppService:
    """ReservaAppService.ReservarClase() - CU-02/CU-03/CU-04. Solo orquesta."""

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def reservar(self, clase_id: str, socio_id: str) -> ResultadoSolicitud:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            membresia = _membresia_vigente(uow, socio_id, ahora)
            resultado = solicitar_lugar(clase, membresia, socio_id, ahora)
            uow.clases.save(clase)
            uow.membresias.save(membresia)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return resultado

    def reservar_con_pago(self, clase_id: str, socio_id: str, referencia_pago: str) -> ResultadoSolicitud:
        """CU-04 / US-12: cobro en mostrador de una clase fuera de plan."""
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            membresia = _membresia_vigente(uow, socio_id, ahora)
            ctx = validar_elegibilidad(clase, membresia, socio_id, ahora)
            if PlanIncluyeServicio().is_satisfied_by(ctx):
                raise BusinessRuleViolation("El plan ya incluye esta clase: reserva sin cobro", "PLAN_YA_INCLUYE_CLASE")
            if not ClaseConCupo().is_satisfied_by(ctx):
                raise BusinessRuleViolation("La clase está llena: no se cobra sin un lugar disponible", "CLASE_LLENA")

            def operacion(pago):
                resultado = solicitar_lugar(clase, membresia, socio_id, ahora, pago_id=pago.id)
                uow.clases.save(clase)
                return resultado

            resultado = ejecutar_con_cobro(
                d, uow, socio_id, clase.precio_extra, f"CLASE_FUERA_DE_PLAN:{clase.id}",
                referencia_pago, ahora, operacion,
            )
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return resultado

    def cancelar_reserva(self, clase_id: str, reserva_id: str) -> bool:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            tardia = clase.cancelar_reserva(reserva_id, ahora, d.reglas.limite_cancelacion)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)  # LugarLiberado -> ListaEsperaAppService.asignar_vacante
        return tardia

    def abandonar_lista_espera(self, clase_id: str, socio_id: str) -> None:
        with self.deps.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            clase.abandonar_lista_espera(socio_id)
            uow.clases.save(clase)
            uow.commit()
