from __future__ import annotations

from ..domain.entrenamiento import SERVICIO_ENTRENAMIENTO, PaqueteEntrenamiento, validar_membresia_para_paquete
from ..domain.errors import AccesoDenegadoError, InvalidData, NotFound
from .context import Dependencias
from .membresia_service import socio_o_404
from .pagos import ejecutar_con_cobro


class EntrenamientoAppService:
    """US-13: contratación de paquetes de entrenamiento personal."""

    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def contratar(self, socio_id: str, instructor_id: str, sesiones: int, referencia_pago: str) -> PaqueteEntrenamiento:
        d, ahora = self.deps, self.deps.reloj()
        if isinstance(sesiones, bool) or sesiones <= 0:
            raise InvalidData("El paquete debe tener al menos una sesión")
        with d.uow_factory() as uow:
            socio_o_404(uow, socio_id)
            if uow.instructores.get(instructor_id) is None:
                raise NotFound("El instructor no existe")
            membresia = uow.membresias.get_por_socio(socio_id)
            if membresia is None:
                raise AccesoDenegadoError("El socio no tiene una membresía contratada", ["SIN_MEMBRESIA"])
            membresia.refrescar_estado(ahora)
            validar_membresia_para_paquete(membresia, ahora)  # antes de cobrar

            if membresia.plan.incluye(SERVICIO_ENTRENAMIENTO):  # el plan lo incluye: no se cobra
                paquete = PaqueteEntrenamiento.contratar(membresia, instructor_id, sesiones, None, ahora)
                uow.entrenamientos.add(paquete)
                uow.commit()
            else:
                def operacion(pago):
                    p = PaqueteEntrenamiento.contratar(membresia, instructor_id, sesiones, pago.id, ahora)
                    uow.entrenamientos.add(p)
                    return p

                paquete = ejecutar_con_cobro(
                    d, uow, socio_id, d.reglas.tarifa_sesion_entrenamiento * sesiones,
                    f"ENTRENAMIENTO_PERSONAL:{sesiones}_SESIONES", referencia_pago, ahora, operacion)
        d.bus.publicar(paquete.extraer_eventos())
        return paquete
