from decimal import Decimal

import pytest

from src.infrastructure.orm import PagoORM


@pytest.mark.us("US-13", "E1")
def test_plan_anual_incluye_el_entrenamiento_y_no_se_cobra(sistema):
    inst, sid = sistema.instructor("Coach"), sistema.con_membresia("Ana", "ANUAL")
    cobros_antes = len(sistema.pasarela.cobros)
    r = sistema.post(f"/socios/{sid}/entrenamiento-personal",
                     json={"instructor_id": inst, "sesiones": 5, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 201
    assert r.json()["modulo_agenda_habilitado"] is True and r.json()["incluido_en_plan"] is True
    assert len(sistema.pasarela.cobros) == cobros_antes


@pytest.mark.us("US-13", "E1")
def test_plan_mensual_adquiere_el_paquete_pagando_por_sesion(sistema):
    inst, sid = sistema.instructor("Coach"), sistema.con_membresia("Beto", "MENSUAL")
    r = sistema.post(f"/socios/{sid}/entrenamiento-personal",
                     json={"instructor_id": inst, "sesiones": 4, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 201 and r.json()["incluido_en_plan"] is False
    assert sistema.pasarela.cobros[-1][1] == Decimal("1200.00")  # 4 sesiones x $300
    with sistema.container.session_factory() as s:
        assert s.query(PagoORM).filter(PagoORM.concepto.like("ENTRENAMIENTO%")).one().estado == "APROBADO"


@pytest.mark.us("US-13", "E2")
def test_membresia_vencida_bloquea_la_compra_solicitando_renovar_y_no_cobra(sistema):
    inst = sistema.instructor("Coach")
    sid = sistema.con_membresia("Carla", "MENSUAL", fecha_inicio="2026-08-01")
    cobros = len(sistema.pasarela.cobros)
    r = sistema.post(f"/socios/{sid}/entrenamiento-personal",
                     json={"instructor_id": inst, "sesiones": 4, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 403 and "renuévala" in r.json()["mensaje"]
    assert len(sistema.pasarela.cobros) == cobros  # no se cobró nada


def test_entrenamiento_casos_invalidos(sistema):
    inst = sistema.instructor("Coach")
    sid = sistema.con_membresia("Diego", "MENSUAL")
    cuerpo = {"instructor_id": inst, "sesiones": 3, "referencia_pago": "TARJETA-OK"}
    assert sistema.post(f"/socios/{sid}/entrenamiento-personal", json={**cuerpo, "sesiones": 0}).status_code == 422
    assert sistema.post(f"/socios/{sid}/entrenamiento-personal", json={**cuerpo, "instructor_id": "x"}).status_code == 404
    assert sistema.post("/socios/fantasma/entrenamiento-personal", json=cuerpo).status_code == 404
    r = sistema.post(f"/socios/{sid}/entrenamiento-personal", json={**cuerpo, "referencia_pago": "FAIL-1"})
    assert r.status_code == 402
    sin_plan = sistema.socio("Sin Plan")
    assert sistema.post(f"/socios/{sin_plan}/entrenamiento-personal", json=cuerpo).json()["codigo"] == "ACCESO_DENEGADO"
    sistema.post(f"/socios/{sid}/suspension", json={"motivo": "Adeudo"})
    assert sistema.post(f"/socios/{sid}/entrenamiento-personal", json=cuerpo).status_code == 403
