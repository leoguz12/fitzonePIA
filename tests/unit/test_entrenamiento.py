from datetime import date

import pytest

from src.domain.entrenamiento import PaqueteEntrenamiento
from src.domain.errors import AccesoDenegadoError, InvalidData
from src.domain.events import PaqueteEntrenamientoContratado
from src.domain.value_objects import TipoPlan
from tests.factories import AHORA, membresia


@pytest.mark.us("US-13", "E1")
def test_membresia_activa_puede_contratar_y_habilita_el_modulo_de_agenda():
    m = membresia(TipoPlan.ANUAL)
    p = PaqueteEntrenamiento.contratar(m, "inst-1", 5, None, AHORA)
    assert p.modulo_agenda_habilitado and p.incluido_en_plan  # el plan anual lo incluye
    assert isinstance(p.extraer_eventos()[0], PaqueteEntrenamientoContratado)
    assert not PaqueteEntrenamiento.contratar(membresia(TipoPlan.MENSUAL), "inst-1", 5, "pago-1", AHORA).incluido_en_plan


@pytest.mark.us("US-13", "E2")
def test_membresia_vencida_bloquea_la_compra_y_pide_renovar():
    vencida = membresia(TipoPlan.MENSUAL, inicio=date(2026, 8, 1))
    with pytest.raises(AccesoDenegadoError) as e:
        PaqueteEntrenamiento.contratar(vencida, "inst-1", 5, "pago-1", AHORA)
    assert "renuévala" in e.value.mensaje and e.value.codigos == ["MEMBRESIA_VENCIDA"]


def test_membresia_suspendida_tambien_bloquea():
    m = membresia()
    m.suspender("Adeudo", AHORA)
    with pytest.raises(AccesoDenegadoError) as e:
        PaqueteEntrenamiento.contratar(m, "inst-1", 5, None, AHORA)
    assert "suspendida" in e.value.mensaje


@pytest.mark.parametrize("sesiones", [0, -3, True, 2.5])
def test_el_paquete_requiere_al_menos_una_sesion(sesiones):
    with pytest.raises(InvalidData):
        PaqueteEntrenamiento.contratar(membresia(), "inst-1", sesiones, None, AHORA)
