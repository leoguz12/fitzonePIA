"""Modelos ORM (SQLAlchemy 2.0). Viven SOLO en infraestructura: el dominio no los conoce."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SocioORM(Base):
    __tablename__ = "socios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160))
    advertencias: Mapped[int] = mapped_column(Integer, default=0)
    no_shows: Mapped[int] = mapped_column(Integer, default=0)


class MembresiaORM(Base):
    __tablename__ = "membresias"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    socio_id: Mapped[str] = mapped_column(ForeignKey("socios.id"), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    servicios: Mapped[str] = mapped_column(Text)
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20))
    motivo_suspension: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InstructorORM(Base):
    __tablename__ = "instructores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))


class ReservaORM(Base):
    __tablename__ = "reservas"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    clase_id: Mapped[str] = mapped_column(ForeignKey("clases.id"), index=True)
    socio_id: Mapped[str] = mapped_column(ForeignKey("socios.id"), index=True)
    estado: Mapped[str] = mapped_column(String(20))
    creada_en: Mapped[datetime] = mapped_column(DateTime)
    pago_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    cancelada_tarde: Mapped[bool] = mapped_column(Boolean, default=False)


class ListaEsperaORM(Base):
    __tablename__ = "lista_espera"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clase_id: Mapped[str] = mapped_column(ForeignKey("clases.id"), index=True)
    socio_id: Mapped[str] = mapped_column(String(36))
    posicion: Mapped[int] = mapped_column(Integer)
    agregado_en: Mapped[datetime] = mapped_column(DateTime)


class ClaseORM(Base):
    __tablename__ = "clases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    instructor_id: Mapped[str] = mapped_column(ForeignKey("instructores.id"))
    instructor_suplente_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    inicio: Mapped[datetime] = mapped_column(DateTime, index=True)
    duracion_min: Mapped[int] = mapped_column(Integer)
    capacidad: Mapped[int] = mapped_column(Integer)
    servicio_requerido: Mapped[str] = mapped_column(String(60))
    precio_extra: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(20))
    motivo_cancelacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reservas: Mapped[list[ReservaORM]] = relationship(
        cascade="all, delete-orphan", order_by="ReservaORM.creada_en", lazy="selectin"
    )
    lista_espera: Mapped[list[ListaEsperaORM]] = relationship(
        cascade="all, delete-orphan", order_by="ListaEsperaORM.posicion", lazy="selectin"
    )


class PagoORM(Base):
    __tablename__ = "pagos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    socio_id: Mapped[str] = mapped_column(ForeignKey("socios.id"), index=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    concepto: Mapped[str] = mapped_column(String(160))
    estado: Mapped[str] = mapped_column(String(20))
    referencia_externa: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime)


class PaqueteEntrenamientoORM(Base):
    __tablename__ = "paquetes_entrenamiento"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    socio_id: Mapped[str] = mapped_column(ForeignKey("socios.id"), index=True)
    instructor_id: Mapped[str] = mapped_column(ForeignKey("instructores.id"))
    sesiones: Mapped[int] = mapped_column(Integer)
    pago_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    incluido_en_plan: Mapped[bool] = mapped_column(Boolean)
    creado_en: Mapped[datetime] = mapped_column(DateTime)


class AccesoORM(Base):
    __tablename__ = "accesos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    socio_id: Mapped[str] = mapped_column(String(36), index=True)
    permitido: Mapped[bool] = mapped_column(Boolean)
    motivo: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    advertencia: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime)


class NotificacionORM(Base):
    __tablename__ = "notificaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    socio_id: Mapped[str] = mapped_column(String(36), index=True)
    asunto: Mapped[str] = mapped_column(String(160))
    mensaje: Mapped[str] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(DateTime)
