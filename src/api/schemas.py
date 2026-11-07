"""Esquemas de entrada/salida (DTOs) de la API REST."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from ..domain.membresia import Membresia, ResultadoAcceso
from ..domain.socio import Socio
from ..domain.value_objects import TipoPlan


class SocioIn(BaseModel):
    nombre: str = Field(examples=["Ana Torres"])
    email: str = Field(examples=["ana@fitzone.mx"])


class SocioOut(BaseModel):
    id: str
    nombre: str
    email: str
    advertencias: int
    no_shows: int


def socio_out(s: Socio) -> SocioOut:
    return SocioOut(id=s.id, nombre=s.nombre, email=s.email, advertencias=s.advertencias, no_shows=s.no_shows)


class ContratarIn(BaseModel):
    tipo: TipoPlan = Field(examples=["TRIMESTRAL"])
    referencia_pago: str = Field(examples=["TARJETA-4242"], description="Empieza con FAIL para simular un rechazo")
    fecha_inicio: Optional[date] = None


class PlanIn(BaseModel):
    tipo: TipoPlan
    referencia_pago: str = Field(examples=["TARJETA-4242"])


class SuspensionIn(BaseModel):
    motivo: str = Field(examples=["Pago pendiente"])


class MembresiaOut(BaseModel):
    id: str
    socio_id: str
    tipo: TipoPlan
    servicios_incluidos: list[str]
    fecha_inicio: date
    fecha_vencimiento: date
    estado: str
    motivo_suspension: Optional[str]


def membresia_out(m: Membresia) -> MembresiaOut:
    return MembresiaOut(
        id=m.id, socio_id=m.socio_id, tipo=m.plan.tipo, servicios_incluidos=sorted(m.plan.servicios_incluidos),
        fecha_inicio=m.vigencia.fecha_inicio, fecha_vencimiento=m.vigencia.fecha_vencimiento,
        estado=m.estado.value, motivo_suspension=m.motivo_suspension,
    )


class AccesoIn(BaseModel):
    socio_id: str


class AccesoOut(BaseModel):
    permitido: bool
    alerta: Optional[str] = Field(None, description="ROJA cuando se deniega el paso")
    codigo: Optional[str]
    mensaje: str
    advertencia: Optional[str]
    reservas_hoy: list[dict] = Field(default_factory=list, description="Clases reservadas por el socio para hoy (US-14)")


def acceso_out(r: ResultadoAcceso, reservas_hoy: Optional[list[dict]] = None) -> AccesoOut:
    return AccesoOut(permitido=r.permitido, alerta=None if r.permitido else "ROJA", codigo=r.codigo,
                     mensaje=r.mensaje, advertencia=r.advertencia, reservas_hoy=reservas_hoy or [])


class InstructorIn(BaseModel):
    nombre: str = Field(examples=["Laura Pérez"])


class ClaseIn(BaseModel):
    nombre: str = Field(examples=["Yoga Matutino"])
    instructor_id: str
    inicio: datetime = Field(examples=["2026-11-10T07:00:00"], description="Hora local del gimnasio")
    duracion_min: int = Field(examples=[60])
    capacidad: int = Field(examples=[15])
    servicio_requerido: str = Field(examples=["yoga"], description="Servicio que debe incluir el plan del socio")
    precio_extra: Decimal = Field(examples=["150.00"], description="Costo si el plan no incluye la clase")


class SocioRefIn(BaseModel):
    socio_id: str


class PagoClaseIn(BaseModel):
    socio_id: str
    referencia_pago: str = Field(examples=["TARJETA-4242"])


class CancelarSesionIn(BaseModel):
    instructor_id: str
    motivo: str = Field(examples=["Instructor enfermo"])


class EntrenamientoIn(BaseModel):
    instructor_id: str
    sesiones: int = Field(examples=[5])
    referencia_pago: str = Field(examples=["TARJETA-OK"], description="Se ignora si el plan ya incluye el servicio")


class SuplenteIn(BaseModel):
    instructor_id: str
