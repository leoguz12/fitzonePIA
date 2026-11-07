"""Fábricas de objetos de dominio para las pruebas."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.domain.clase_especial import ClaseEspecial
from src.domain.membresia import Membresia
from src.domain.value_objects import TipoPlan

AHORA = datetime(2026, 11, 9, 10, 0)  # lunes 10:00
TOLERANCIA = timedelta(minutes=10)
LIMITE_CANCELACION = timedelta(hours=2)


def membresia(tipo=TipoPlan.ANUAL, inicio=date(2026, 11, 1), socio_id="socio-1", ahora=AHORA):
    return Membresia.nueva(socio_id, tipo, inicio, ahora)


def clase(capacidad=2, inicio=None, servicio="yoga", instructor="inst-1", precio="150.00", duracion=60):
    inicio = inicio or AHORA + timedelta(hours=8)  # 18:00
    return ClaseEspecial.programar(
        "Yoga Vespertino", instructor, inicio, duracion, capacidad, servicio, Decimal(precio)
    )
