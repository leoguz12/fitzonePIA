from __future__ import annotations

from ..domain.events import AccesoDenegado
from ..domain.membresia import ResultadoAcceso
from .context import Dependencias
from .membresia_service import socio_o_404


class AccesoAppService:
    """AccesoAppService.ValidarIngreso() - CU-01 (orquesta; las reglas viven en Membresia)."""

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def validar_ingreso(self, socio_id: str) -> ResultadoAcceso:
        ahora = self.deps.reloj()
        with self.deps.uow_factory() as uow:
            socio_o_404(uow, socio_id)
            membresia = uow.membresias.get_por_socio(socio_id)
            if membresia is None:
                resultado = ResultadoAcceso(False, "SIN_MEMBRESIA", "El socio no tiene una membresía contratada")
                eventos = [AccesoDenegado(socio_id=socio_id, motivo="SIN_MEMBRESIA", ocurrido_en=ahora)]
            else:
                resultado = membresia.validar_acceso(ahora)
                uow.membresias.save(membresia)  # persiste el recálculo ACTIVA -> VENCIDA
                eventos = membresia.extraer_eventos()
            uow.commit()
        self.deps.bus.publicar(eventos)
        return resultado
