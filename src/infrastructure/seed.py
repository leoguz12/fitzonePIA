"""Datos de demostración (activar con SEED_DEMO_DATA=true). Solo se siembra si la BD está vacía."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from ..application.context import Dependencias
from ..domain.clase_especial import ClaseEspecial
from ..domain.instructor import Instructor
from ..domain.membresia import Membresia
from ..domain.socio import Socio
from ..domain.value_objects import PlanContratado, TipoPlan, Vigencia
from .orm import SocioORM


def sembrar_datos_demo(deps: Dependencias, session_factory) -> dict:
    with session_factory() as s:
        if s.execute(select(func.count()).select_from(SocioORM)).scalar_one() > 0:
            return {}
    ahora = deps.reloj()
    hoy = ahora.date()
    manana = (ahora + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    ids: dict[str, str] = {}
    with deps.uow_factory() as uow:
        laura, mario = Instructor.registrar("Laura Pérez"), Instructor.registrar("Mario Ruiz")
        uow.instructores.add(laura); uow.instructores.add(mario)
        ids.update(instructor_laura=laura.id, instructor_mario=mario.id)

        socios = {
            "ana_anual": (Socio.registrar("Ana Torres", "ana@fitzone.mx"), TipoPlan.ANUAL, hoy - timedelta(days=30)),
            "beto_mensual": (Socio.registrar("Beto Salinas", "beto@fitzone.mx"), TipoPlan.MENSUAL, hoy - timedelta(days=5)),
            "carla_suspendida": (Socio.registrar("Carla Núñez", "carla@fitzone.mx"), TipoPlan.ANUAL, hoy - timedelta(days=60)),
            "diego_vencida": (Socio.registrar("Diego Ramos", "diego@fitzone.mx"), TipoPlan.MENSUAL, hoy - timedelta(days=90)),
            "eva_trimestral": (Socio.registrar("Eva Lozano", "eva@fitzone.mx"), TipoPlan.TRIMESTRAL, hoy - timedelta(days=10)),
        }
        for clave, (socio, tipo, inicio) in socios.items():
            uow.socios.add(socio)
            uow.commit()  # el socio debe existir antes de su membresía (FK)
            membresia = Membresia(f"m-{socio.id}", socio.id, PlanContratado.de_tipo(tipo), Vigencia.desde(inicio, tipo))
            if clave == "carla_suspendida":
                membresia.suspender("Pago pendiente de la anualidad", ahora)
            uow.membresias.add(membresia)
            ids[clave] = socio.id
        uow.commit()

        yoga = ClaseEspecial.programar("Yoga Matutino", laura.id, manana, 60, 2, "yoga", Decimal("150.00"))
        spinning = ClaseEspecial.programar("Spinning Express", mario.id, manana.replace(hour=18), 45, 20, "spinning", Decimal("120.00"))
        funcional = ClaseEspecial.programar("Funcional Total", laura.id, manana.replace(hour=9), 50, 15, "funcional", Decimal("100.00"))
        for c in (yoga, spinning, funcional):
            uow.clases.add(c)
        uow.commit()
        ids.update(clase_yoga_cap2=yoga.id, clase_spinning=spinning.id, clase_funcional=funcional.id)
    return ids
