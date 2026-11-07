from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ..domain.clase_especial import ClaseEspecial
from ..domain.errors import NotFound
from ..domain.instructor import Instructor
from .context import Dependencias
from .reserva_service import clase_o_404


class ClaseAppService:
    def __init__(self, deps: Dependencias) -> None:
        self.deps = deps

    def registrar_instructor(self, nombre: str) -> Instructor:
        instructor = Instructor.registrar(nombre)
        with self.deps.uow_factory() as uow:
            uow.instructores.add(instructor)
            uow.commit()
        return instructor

    def programar(self, nombre: str, instructor_id: str, inicio: datetime, duracion_min: int,
                  capacidad: int, servicio_requerido: str, precio_extra: Decimal) -> ClaseEspecial:
        clase = ClaseEspecial.programar(nombre, instructor_id, inicio, duracion_min, capacidad,
                                        servicio_requerido, precio_extra)
        with self.deps.uow_factory() as uow:
            if uow.instructores.get(instructor_id) is None:
                raise NotFound("El instructor no existe")
            uow.clases.add(clase)
            uow.commit()
        return clase

    def cancelar_sesion(self, clase_id: str, instructor_id: str, motivo: str) -> tuple[str, ...]:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            afectados = clase.cancelar_sesion(instructor_id, motivo, ahora)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return afectados

    def asignar_suplente(self, clase_id: str, instructor_id: str) -> ClaseEspecial:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            if uow.instructores.get(instructor_id) is None:
                raise NotFound("El instructor suplente no existe")
            clase = clase_o_404(uow, clase_id, bloquear=True)
            clase.asignar_suplente(instructor_id, ahora)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return clase

    def finalizar(self, clase_id: str) -> ClaseEspecial:
        d, ahora = self.deps, self.deps.reloj()
        with d.uow_factory() as uow:
            clase = clase_o_404(uow, clase_id, bloquear=True)
            clase.finalizar(ahora)
            uow.clases.save(clase)
            uow.commit()
            eventos = clase.extraer_eventos()
        d.bus.publicar(eventos)
        return clase
