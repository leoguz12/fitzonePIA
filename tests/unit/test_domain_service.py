from datetime import date

import pytest

from src.domain.errors import AccesoDenegadoError, BusinessRuleViolation, PlanNoIncluyeClaseError
from src.domain.services import solicitar_lugar
from src.domain.value_objects import TipoPlan
from tests.factories import AHORA, clase, membresia


@pytest.mark.us("US-02", "E1")
def test_socio_con_plan_que_incluye_la_clase_obtiene_lugar_confirmado():
    c = clase()
    res = solicitar_lugar(c, membresia(TipoPlan.ANUAL), "socio-1", AHORA)
    assert res.tipo == "CONFIRMADA" and res.reserva.socio_id == "socio-1"


@pytest.mark.us("US-02", "E2")
def test_clase_fuera_de_plan_se_bloquea_y_pide_pago_adicional():
    c = clase(servicio="yoga", precio="150.00")
    with pytest.raises(PlanNoIncluyeClaseError) as e:
        solicitar_lugar(c, membresia(TipoPlan.MENSUAL), "socio-1", AHORA)
    assert str(e.value.monto) == "150.00" and c.ocupados == 0


@pytest.mark.us("US-03", "E1")
def test_clase_llena_envia_al_socio_a_la_lista_de_espera():
    c = clase(capacidad=1)
    solicitar_lugar(c, membresia(socio_id="a"), "a", AHORA)
    res = solicitar_lugar(c, membresia(socio_id="b"), "b", AHORA)
    assert res.tipo == "LISTA_ESPERA" and res.posicion == 1


@pytest.mark.us("US-01", "E2")
def test_membresia_vencida_o_suspendida_no_puede_reservar():
    vencida = membresia(TipoPlan.MENSUAL, inicio=date(2026, 8, 1))
    with pytest.raises(AccesoDenegadoError) as e:
        solicitar_lugar(clase(), vencida, "socio-1", AHORA)
    assert "MEMBRESIA_VENCIDA" in e.value.codigos
    suspendida = membresia()
    suspendida.suspender("Adeudo", AHORA)
    with pytest.raises(AccesoDenegadoError) as e:
        solicitar_lugar(clase(), suspendida, "socio-1", AHORA)
    assert e.value.codigos == ["MEMBRESIA_SUSPENDIDA"]


def test_no_permite_reserva_duplicada_ni_clase_cancelada_ni_iniciada():
    c = clase()
    m = membresia()
    solicitar_lugar(c, m, "socio-1", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        solicitar_lugar(c, m, "socio-1", AHORA)
    assert e.value.codigo == "RESERVA_DUPLICADA"
    with pytest.raises(BusinessRuleViolation) as e:
        solicitar_lugar(clase(), m, "otro", c.inicio)
    assert e.value.codigo == "CLASE_YA_INICIADA"


@pytest.mark.us("US-12", "E1")
def test_con_pago_aprobado_reserva_aunque_el_plan_no_incluya_la_clase():
    c = clase(servicio="crossfit")
    res = solicitar_lugar(c, membresia(TipoPlan.MENSUAL), "socio-1", AHORA, pago_id="pago-1")
    assert res.tipo == "CONFIRMADA" and res.reserva.pago_id == "pago-1"


def test_con_pago_pero_clase_llena_no_va_a_lista_de_espera():
    c = clase(capacidad=1, servicio="crossfit")
    solicitar_lugar(c, membresia(TipoPlan.ANUAL, socio_id="a"), "a", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        solicitar_lugar(c, membresia(TipoPlan.MENSUAL, socio_id="b"), "b", AHORA, pago_id="pago-1")
    assert e.value.codigo == "CLASE_LLENA"
