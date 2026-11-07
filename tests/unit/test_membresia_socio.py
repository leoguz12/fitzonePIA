from datetime import date, datetime

import pytest

from src.domain.errors import BusinessRuleViolation, InvalidData, InvalidTransition
from src.domain.events import (
    AccesoDenegado, AccesoPermitido, MembresiaContratada, MembresiaMejorada, MembresiaReactivada,
    MembresiaRenovada, MembresiaSuspendida,
)
from src.domain.instructor import Instructor
from src.domain.membresia import EstadoMembresia
from src.domain.pago import EstadoPago, Pago
from src.domain.socio import Socio
from src.domain.value_objects import TipoPlan
from tests.factories import AHORA, membresia


@pytest.mark.us("US-01", "E1")
def test_acceso_exitoso_con_membresia_vigente_registra_evento():
    m = membresia()
    r = m.validar_acceso(AHORA)
    assert r.permitido and r.codigo is None and r.advertencia is None
    assert isinstance(m.extraer_eventos()[-1], AccesoPermitido)


@pytest.mark.us("US-01", "E2")
def test_membresia_vencida_arroja_alerta_y_deniega():
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 9, 1))  # vence 2026-10-01
    r = m.validar_acceso(AHORA)
    assert not r.permitido and r.codigo == "MEMBRESIA_VENCIDA"
    assert m.estado == EstadoMembresia.VENCIDA  # el estado se recalcula con la fecha
    assert isinstance(m.extraer_eventos()[-1], AccesoDenegado)


@pytest.mark.us("US-06", "E1")
def test_suspendida_muestra_motivo_y_bloquea():
    m = membresia()
    m.suspender("Pago pendiente", AHORA)
    r = m.validar_acceso(AHORA)
    assert not r.permitido and r.codigo == "MEMBRESIA_SUSPENDIDA"
    assert "Pago pendiente" in r.mensaje


@pytest.mark.us("US-06", "E2")
def test_regularizacion_restaura_privilegios():
    m = membresia()
    m.suspender("Pago pendiente", AHORA)
    m.reactivar(AHORA)
    assert m.estado == EstadoMembresia.ACTIVA and m.motivo_suspension is None
    assert m.validar_acceso(AHORA).permitido
    assert any(isinstance(e, MembresiaReactivada) for e in m.extraer_eventos())


def test_reactivar_una_suspension_ya_vencida_deja_la_membresia_vencida():
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 8, 1))
    m.suspender("Adeudo", AHORA)
    m.reactivar(AHORA)
    assert m.estado == EstadoMembresia.VENCIDA


def test_suspender_requiere_motivo_y_estado_activo():
    m = membresia()
    with pytest.raises(InvalidData):
        m.suspender("  ", AHORA)
    m.suspender("x", AHORA)
    with pytest.raises(InvalidTransition):
        m.suspender("otra vez", AHORA)
    with pytest.raises(InvalidTransition):
        membresia().reactivar(AHORA)


def test_acceso_el_ultimo_dia_incluye_advertencia():  # CP-06 de la matriz U5
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 10, 9))  # vence 2026-11-09
    r = m.validar_acceso(AHORA)
    assert r.permitido and "justo a tiempo" in r.advertencia


def test_contratar_registra_evento_y_vigencia():
    m = membresia(TipoPlan.TRIMESTRAL, inicio=date(2026, 11, 6))
    assert m.vigencia.fecha_vencimiento == date(2027, 2, 6)
    assert isinstance(m.extraer_eventos()[0], MembresiaContratada)


@pytest.mark.us("US-11", "E2")
def test_mejora_a_anual_cuenta_desde_el_fin_del_mes_actual():
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 11, 1))
    m.mejorar_plan(TipoPlan.ANUAL, datetime(2026, 11, 9, 10, 0))
    assert m.plan.tipo == TipoPlan.ANUAL
    assert m.vigencia.fecha_vencimiento == date(2027, 11, 30)  # fin de nov-2026 + 12 meses
    assert any(isinstance(e, MembresiaMejorada) for e in m.extraer_eventos())


def test_mejora_invalida_si_no_es_de_mayor_nivel_o_no_esta_activa():
    m = membresia(TipoPlan.ANUAL)
    with pytest.raises(BusinessRuleViolation):
        m.mejorar_plan(TipoPlan.MENSUAL, AHORA)
    vencida = membresia(TipoPlan.MENSUAL, inicio=date(2026, 8, 1))
    with pytest.raises(InvalidTransition):
        vencida.mejorar_plan(TipoPlan.ANUAL, AHORA)


def test_renovar_extiende_desde_el_vencimiento_si_sigue_vigente():
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 11, 1))  # vence 2026-12-01
    m.renovar(TipoPlan.TRIMESTRAL, AHORA)
    assert m.vigencia.fecha_inicio == date(2026, 11, 1)
    assert m.vigencia.fecha_vencimiento == date(2027, 3, 1)
    assert any(isinstance(e, MembresiaRenovada) for e in m.extraer_eventos())


def test_renovar_vencida_empieza_hoy_y_suspendida_no_puede_renovar():
    m = membresia(TipoPlan.MENSUAL, inicio=date(2026, 8, 1))
    m.renovar(TipoPlan.MENSUAL, AHORA)
    assert m.estado == EstadoMembresia.ACTIVA
    assert m.vigencia.fecha_inicio == date(2026, 11, 9)
    s = membresia()
    s.suspender("x", AHORA)
    with pytest.raises(InvalidTransition):
        s.renovar(TipoPlan.MENSUAL, AHORA)
    assert any(isinstance(e, MembresiaSuspendida) for e in s.extraer_eventos())


def test_socio_valida_contacto_y_cuenta_sanciones():
    s = Socio.registrar("Ana", "ana@correo.com")
    s.registrar_advertencia(); s.registrar_no_show()
    assert (s.advertencias, s.no_shows) == (1, 1)
    for nombre, email in [("", "a@b.com"), ("Ana", "sin-arroba"), ("Ana", "a@b"), ("Ana", "@b.com")]:
        with pytest.raises(InvalidData):
            Socio.registrar(nombre, email)


def test_instructor_requiere_nombre():
    assert Instructor.registrar("Laura").nombre == "Laura"
    with pytest.raises(InvalidData):
        Instructor.registrar(" ")


def test_pago_valida_monto_y_permite_reembolso_solo_si_aprobado():
    p = Pago.registrar("s1", 150, "CLASE", True, "REF-1", AHORA)
    assert p.aprobado
    p.reembolsar()
    assert p.estado == EstadoPago.REEMBOLSADO
    with pytest.raises(InvalidTransition):
        p.reembolsar()
    with pytest.raises(InvalidData):
        Pago.registrar("s1", 0, "CLASE", True, None, AHORA)
    with pytest.raises(InvalidData):
        Pago.registrar("s1", 10, " ", True, None, AHORA)
    assert not Pago.registrar("s1", 10, "X", False, None, AHORA).aprobado
