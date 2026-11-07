"""Lado de lectura de CQRS: consultas SQL directas, sin cargar agregados (ADR 0003)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import sessionmaker

from ..application.ports import ReadModel
from .orm import AccesoORM, ClaseORM, ListaEsperaORM, NotificacionORM, ReservaORM

_C, _R, _LE = ClaseORM.__table__, ReservaORM.__table__, ListaEsperaORM.__table__
_OCUPAN = ("CONFIRMADA", "ASISTIDA")


def _contar(*estados: str):
    return func.coalesce(func.sum(case((_R.c.estado.in_(estados), 1), else_=0)), 0)


def _consulta_metricas():
    espera = select(func.count()).select_from(_LE).where(_LE.c.clase_id == _C.c.id).scalar_subquery()
    columnas = [_C.c.id, _C.c.nombre, _C.c.inicio, _C.c.capacidad, _C.c.estado, _C.c.instructor_id,
                _C.c.instructor_suplente_id, _C.c.servicio_requerido, _C.c.precio_extra]
    stmt = (
        select(*columnas, _contar(*_OCUPAN).label("activas"), _contar("ASISTIDA").label("asistencias"),
               _contar("NO_SHOW").label("no_shows"), _contar("CANCELADA").label("cancelaciones"),
               espera.label("en_espera"))
        .select_from(_C.outerjoin(_R, _R.c.clase_id == _C.c.id))
        .group_by(*columnas)
    )
    return stmt


def _fila_a_dict(f) -> dict[str, Any]:
    activas, capacidad = int(f.activas), int(f.capacidad)
    return {
        "clase_id": f.id,
        "nombre": f.nombre,
        "inicio": f.inicio,
        "estado": f.estado,
        "servicio_requerido": f.servicio_requerido,
        "instructor_id": f.instructor_id,
        "instructor_suplente_id": f.instructor_suplente_id,
        "capacidad": capacidad,
        "inscritos": activas,
        "cupos_disponibles": max(capacidad - activas, 0),
        "en_lista_espera": int(f.en_espera),
        "asistencias": int(f.asistencias),
        "no_shows": int(f.no_shows),
        "cancelaciones": int(f.cancelaciones),
        "precio_extra": f.precio_extra,
    }


class SqlReadModel(ReadModel):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def _ejecutar(self, stmt):
        with self._sf() as s:
            return s.execute(stmt).all()

    def catalogo(self, ahora: datetime) -> list[dict[str, Any]]:
        stmt = _consulta_metricas().where(_C.c.estado == "PROGRAMADA", _C.c.inicio >= ahora).order_by(_C.c.inicio)
        return [_fila_a_dict(f) for f in self._ejecutar(stmt)]

    def aforo(self, clase_id: str) -> Optional[dict[str, Any]]:
        filas = self._ejecutar(_consulta_metricas().where(_C.c.id == clase_id))
        if not filas:
            return None
        d = _fila_a_dict(filas[0])
        d["resumen"] = f"{d['inscritos']} inscritos de {d['capacidad']}"
        return d

    def clases_instructor(self, instructor_id: str, fecha: date) -> list[dict[str, Any]]:
        desde = datetime.combine(fecha, time.min)
        stmt = (
            _consulta_metricas()
            .where(or_(_C.c.instructor_id == instructor_id, _C.c.instructor_suplente_id == instructor_id),
                   _C.c.inicio >= desde, _C.c.inicio < desde + timedelta(days=1))
            .order_by(_C.c.inicio)
        )
        filas = []
        for f in self._ejecutar(stmt):
            d = _fila_a_dict(f)
            d["resumen"] = f"{d['inscritos']} inscritos de {d['capacidad']}"  # US-08 E2: "0 inscritos"
            filas.append(d)
        return filas

    def reporte_demanda(self, desde: date, hasta: date) -> dict[str, Any]:
        ini = datetime.combine(desde, time.min)
        fin = datetime.combine(hasta, time.min) + timedelta(days=1)
        stmt = _consulta_metricas().where(_C.c.inicio >= ini, _C.c.inicio < fin).order_by(_C.c.inicio)
        clases = []
        for f in self._ejecutar(stmt):
            d = _fila_a_dict(f)
            d["tasa_ocupacion"] = round(100 * d["inscritos"] / d["capacidad"], 2)
            d["lugares_vacios"] = d["cupos_disponibles"]
            clases.append(d)
        vigentes = [c for c in clases if c["estado"] != "CANCELADA"]
        asistencias = sum(c["asistencias"] for c in vigentes)
        no_shows = sum(c["no_shows"] for c in vigentes)
        resumen = {
            "total_clases": len(clases),
            "clases_canceladas": len(clases) - len(vigentes),
            "tasa_ocupacion_promedio": round(sum(c["tasa_ocupacion"] for c in vigentes) / len(vigentes), 2) if vigentes else 0.0,
            "lugares_vacios_total": sum(c["lugares_vacios"] for c in vigentes),
            "tasa_no_show": round(100 * no_shows / (asistencias + no_shows), 2) if (asistencias + no_shows) else 0.0,
        }
        return {"desde": desde, "hasta": hasta, "resumen": resumen, "clases": clases}

    def reservas_del_dia(self, socio_id: str, dia: date) -> list[dict[str, Any]]:
        ini = datetime.combine(dia, time.min)
        stmt = (
            select(_C.c.id, _C.c.nombre, _C.c.inicio)
            .select_from(_R.join(_C, _R.c.clase_id == _C.c.id))
            .where(_R.c.socio_id == socio_id, _R.c.estado == "CONFIRMADA", _C.c.inicio >= ini,
                   _C.c.inicio < ini + timedelta(days=1))
            .order_by(_C.c.inicio)
        )
        return [{"clase_id": f.id, "nombre": f.nombre, "inicio": f.inicio} for f in self._ejecutar(stmt)]

    def notificaciones(self, socio_id: str) -> list[dict[str, Any]]:
        stmt = select(NotificacionORM.__table__).where(NotificacionORM.socio_id == socio_id).order_by(NotificacionORM.id)
        return [{"asunto": f.asunto, "mensaje": f.mensaje, "creada_en": f.creada_en} for f in self._ejecutar(stmt)]

    def accesos(self, socio_id: str) -> list[dict[str, Any]]:
        stmt = select(AccesoORM.__table__).where(AccesoORM.socio_id == socio_id).order_by(AccesoORM.id)
        return [{"permitido": f.permitido, "motivo": f.motivo, "advertencia": f.advertencia,
                 "ocurrido_en": f.ocurrido_en} for f in self._ejecutar(stmt)]
