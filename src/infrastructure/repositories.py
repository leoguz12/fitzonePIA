"""Implementaciones SQLAlchemy de los puertos de repositorio.

Traducen entre filas ORM y objetos de dominio: el dominio nunca ve SQLAlchemy.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..application.ports import AccesoRepository, Notificacion, NotificacionRepository, RegistroAcceso
from ..domain.clase_especial import (
    ClaseEspecial, EntradaListaEspera, EstadoClase, EstadoReserva, ListaEspera, Reserva,
)
from ..domain.entrenamiento import PaqueteEntrenamiento
from ..domain.instructor import Instructor
from ..domain.membresia import EstadoMembresia, Membresia
from ..domain.pago import EstadoPago, Pago
from ..domain.repositories import (
    ClaseRepository, EntrenamientoRepository, InstructorRepository, MembresiaRepository, PagoRepository, SocioRepository,
)
from ..domain.socio import Socio
from ..domain.value_objects import CapacidadMaxima, PlanContratado, TipoPlan, Vigencia
from .orm import (
    AccesoORM, ClaseORM, InstructorORM, ListaEsperaORM, MembresiaORM, NotificacionORM, PagoORM,
    PaqueteEntrenamientoORM, ReservaORM, SocioORM,
)


class SqlSocioRepository(SocioRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, socio: Socio) -> None:
        self.s.add(SocioORM(id=socio.id, nombre=socio.nombre, email=socio.email,
                            advertencias=socio.advertencias, no_shows=socio.no_shows))

    def get(self, socio_id: str) -> Optional[Socio]:
        r = self.s.get(SocioORM, socio_id)
        return None if r is None else Socio(r.id, r.nombre, r.email, r.advertencias, r.no_shows)

    def save(self, socio: Socio) -> None:
        r = self.s.get(SocioORM, socio.id)
        r.nombre, r.email = socio.nombre, socio.email
        r.advertencias, r.no_shows = socio.advertencias, socio.no_shows


class SqlMembresiaRepository(MembresiaRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, m: Membresia) -> None:
        row = MembresiaORM(id=m.id, socio_id=m.socio_id)
        self._copiar(m, row)
        self.s.add(row)

    @staticmethod
    def _copiar(m: Membresia, row: MembresiaORM) -> None:
        row.tipo = m.plan.tipo.value
        row.servicios = ",".join(sorted(m.plan.servicios_incluidos))
        row.fecha_inicio = m.vigencia.fecha_inicio
        row.fecha_vencimiento = m.vigencia.fecha_vencimiento
        row.estado = m.estado.value
        row.motivo_suspension = m.motivo_suspension

    def get_por_socio(self, socio_id: str) -> Optional[Membresia]:
        row = self.s.query(MembresiaORM).filter_by(socio_id=socio_id).one_or_none()
        if row is None:
            return None
        plan = PlanContratado(TipoPlan(row.tipo), frozenset(row.servicios.split(",")))
        return Membresia(row.id, row.socio_id, plan, Vigencia(row.fecha_inicio, row.fecha_vencimiento),
                         EstadoMembresia(row.estado), row.motivo_suspension)

    def save(self, m: Membresia) -> None:
        self._copiar(m, self.s.get(MembresiaORM, m.id))


class SqlInstructorRepository(InstructorRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, instructor: Instructor) -> None:
        self.s.add(InstructorORM(id=instructor.id, nombre=instructor.nombre))

    def get(self, instructor_id: str) -> Optional[Instructor]:
        r = self.s.get(InstructorORM, instructor_id)
        return None if r is None else Instructor(r.id, r.nombre)


class SqlClaseRepository(ClaseRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    @staticmethod
    def _reserva_orm(clase_id: str, r: Reserva) -> ReservaORM:
        return ReservaORM(id=r.id, clase_id=clase_id, socio_id=r.socio_id, estado=r.estado.value,
                          creada_en=r.creada_en, pago_id=r.pago_id, cancelada_tarde=r.cancelada_tarde)

    @staticmethod
    def _espera_orm(clase: ClaseEspecial) -> list[ListaEsperaORM]:
        return [ListaEsperaORM(clase_id=clase.id, socio_id=e.socio_id, posicion=i, agregado_en=e.agregado_en)
                for i, e in enumerate(clase.lista_espera.entradas, start=1)]

    @staticmethod
    def _copiar_escalares(clase: ClaseEspecial, row: ClaseORM) -> None:
        row.nombre, row.instructor_id = clase.nombre, clase.instructor_id
        row.instructor_suplente_id = clase.instructor_suplente_id
        row.inicio, row.duracion_min = clase.inicio, clase.duracion_min
        row.capacidad = clase.capacidad.limite
        row.servicio_requerido, row.precio_extra = clase.servicio_requerido, clase.precio_extra
        row.estado, row.motivo_cancelacion = clase.estado.value, clase.motivo_cancelacion

    def add(self, clase: ClaseEspecial) -> None:
        row = ClaseORM(id=clase.id)
        self._copiar_escalares(clase, row)
        row.reservas = [self._reserva_orm(clase.id, r) for r in clase.reservas]
        row.lista_espera = self._espera_orm(clase)
        self.s.add(row)

    def get(self, clase_id: str, bloquear: bool = False) -> Optional[ClaseEspecial]:
        row = self.s.get(ClaseORM, clase_id, with_for_update=bloquear)
        if row is None:
            return None
        reservas = [Reserva(r.id, r.socio_id, r.creada_en, EstadoReserva(r.estado), r.pago_id, r.cancelada_tarde)
                    for r in row.reservas]
        espera = ListaEspera(EntradaListaEspera(e.socio_id, e.agregado_en) for e in row.lista_espera)
        return ClaseEspecial(
            row.id, row.nombre, row.instructor_id, row.inicio, row.duracion_min,
            CapacidadMaxima(row.capacidad), row.servicio_requerido, row.precio_extra,
            EstadoClase(row.estado), reservas, espera, row.instructor_suplente_id, row.motivo_cancelacion,
        )

    def save(self, clase: ClaseEspecial) -> None:
        row = self.s.get(ClaseORM, clase.id)
        self._copiar_escalares(clase, row)
        existentes = {r.id: r for r in row.reservas}
        for r in clase.reservas:
            if r.id in existentes:
                orm = existentes[r.id]
                orm.estado, orm.pago_id, orm.cancelada_tarde = r.estado.value, r.pago_id, r.cancelada_tarde
            else:
                row.reservas.append(self._reserva_orm(clase.id, r))
        row.lista_espera = self._espera_orm(clase)  # la cola se reescribe completa (conserva el orden FIFO)


class SqlPagoRepository(PagoRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, pago: Pago) -> None:
        row = self.s.get(PagoORM, pago.id)
        if row is None:
            row = PagoORM(id=pago.id, socio_id=pago.socio_id, monto=pago.monto, concepto=pago.concepto,
                          creado_en=pago.creado_en)
            self.s.add(row)
        row.estado, row.referencia_externa = pago.estado.value, pago.referencia_externa

    def get(self, pago_id: str) -> Optional[Pago]:
        r = self.s.get(PagoORM, pago_id)
        if r is None:
            return None
        return Pago(r.id, r.socio_id, r.monto, r.concepto, EstadoPago(r.estado), r.referencia_externa, r.creado_en)


class SqlAccesoRepository(AccesoRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, registro: RegistroAcceso) -> None:
        self.s.add(AccesoORM(socio_id=registro.socio_id, permitido=registro.permitido, motivo=registro.motivo,
                             advertencia=registro.advertencia, ocurrido_en=registro.ocurrido_en))


class SqlNotificacionRepository(NotificacionRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, n: Notificacion) -> None:
        self.s.add(NotificacionORM(socio_id=n.socio_id, asunto=n.asunto, mensaje=n.mensaje, creada_en=n.creada_en))


class SqlEntrenamientoRepository(EntrenamientoRepository):
    def __init__(self, session: Session) -> None:
        self.s = session

    def add(self, p: PaqueteEntrenamiento) -> None:
        self.s.add(PaqueteEntrenamientoORM(id=p.id, socio_id=p.socio_id, instructor_id=p.instructor_id,
                                           sesiones=p.sesiones, pago_id=p.pago_id,
                                           incluido_en_plan=p.incluido_en_plan, creado_en=p.creado_en))

    def get(self, paquete_id: str) -> Optional[PaqueteEntrenamiento]:
        r = self.s.get(PaqueteEntrenamientoORM, paquete_id)
        if r is None:
            return None
        return PaqueteEntrenamiento(r.id, r.socio_id, r.instructor_id, r.sesiones, r.pago_id,
                                    r.incluido_en_plan, r.creado_en)
