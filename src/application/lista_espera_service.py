from __future__ import annotations

from ..domain.specifications import ContextoAcceso, ContextoReserva, PlanIncluyeServicio, acceso_permitido
from .context import Dependencias
from .reserva_service import clase_o_404


class ListaEsperaAppService:
    """ListaEsperaAppService.AsignarVacante() - CU-03 / US-05.

    Escucha el evento LugarLiberado; la cola FIFO la maneja la entidad ListaEspera.
    """

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def asignar_vacante(self, clase_id: str) -> int:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)

            def es_elegible(socio_id: str) -> bool:
                m = uow.membresias.get_por_socio(socio_id)
                if m is None:
                    return False
                m.refrescar_estado(ahora)
                return acceso_permitido().is_satisfied_by(ContextoAcceso(m, ahora.date())) and (
                    PlanIncluyeServicio().is_satisfied_by(ContextoReserva(m, clase, socio_id, ahora))
                )

            asignadas = clase.asignar_desde_lista_espera(ahora, es_elegible)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return len(asignadas)
