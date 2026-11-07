from datetime import date

import pytest

from src.domain.errors import InvalidData
from src.domain.value_objects import (
    CapacidadMaxima, PlanContratado, TipoPlan, Vigencia, add_months, fin_de_mes,
)


@pytest.mark.us("US-11", "E1")
def test_vigencia_trimestral_vence_exactamente_a_tres_meses():
    v = Vigencia.desde(date(2026, 11, 6), TipoPlan.TRIMESTRAL)
    assert v.fecha_vencimiento == date(2027, 2, 6)


def test_add_months_ajusta_fin_de_mes():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)
    assert add_months(date(2026, 11, 15), 12) == date(2027, 11, 15)


def test_fin_de_mes():
    assert fin_de_mes(date(2026, 2, 10)) == date(2026, 2, 28)
    assert fin_de_mes(date(2028, 2, 10)) == date(2028, 2, 29)


def test_vigencia_rechaza_fechas_invalidas():
    with pytest.raises(InvalidData):
        Vigencia(date(2026, 11, 10), date(2026, 11, 10))
    with pytest.raises(InvalidData):
        Vigencia(date(2026, 11, 10), date(2026, 11, 1))


@pytest.mark.us("US-01", "E2")
def test_vigencia_ultimo_dia_es_valido_y_el_siguiente_no():
    v = Vigencia(date(2026, 10, 1), date(2026, 10, 31))
    assert v.vigente_en(date(2026, 10, 31))
    assert not v.vigente_en(date(2026, 11, 1))
    assert v.vencida_en(date(2026, 11, 1))
    assert not v.vigente_en(date(2026, 9, 30))


def test_plan_contratado_incluye_servicios_segun_catalogo():
    mensual = PlanContratado.de_tipo(TipoPlan.MENSUAL)
    anual = PlanContratado.de_tipo(TipoPlan.ANUAL)
    assert mensual.incluye("funcional") and not mensual.incluye("yoga")
    assert anual.incluye("YOGA")


@pytest.mark.parametrize("valor", [0, -1, 2.5, True, "10", None])
def test_capacidad_maxima_rechaza_valores_invalidos(valor):
    with pytest.raises(InvalidData):
        CapacidadMaxima(valor)


def test_capacidad_maxima_valida():
    assert CapacidadMaxima(15).limite == 15


def test_tipo_plan_niveles_y_meses():
    assert [t.meses for t in TipoPlan] == [1, 3, 12]
    assert TipoPlan.MENSUAL.nivel < TipoPlan.TRIMESTRAL.nivel < TipoPlan.ANUAL.nivel
