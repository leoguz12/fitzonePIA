from __future__ import annotations

from ..domain.clase_especial import ResultadoAsistencia
from .context import Dependencias
from .reserva_service import clase_o_404


class AsistenciaAppService:
    """AsistenciaAppService.MarcarNoShows() - US-07."""

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def registrar_asistencia(self, clase_id: str, socio_id: str) -> ResultadoAsistencia:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            resultado = clase.registrar_asistencia(socio_id, ahora, d.reglas.tolerancia)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return resultado

    def procesar_no_shows(self, clase_id: str) -> list[str]:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            marcadas = clase.procesar_no_shows(ahora, d.reglas.tolerancia)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return [r.socio_id for r in marcadas]
