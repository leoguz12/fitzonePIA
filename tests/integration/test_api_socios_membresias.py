from decimal import Decimal

import pytest


def test_registrar_y_consultar_socio(sistema):
    sid = sistema.socio("Ana Torres")
    assert sistema.socio_datos(sid) == {"id": sid, "nombre": "Ana Torres", "email": "ana.torres@fitzone.mx",
                                       "advertencias": 0, "no_shows": 0}


def test_datos_de_contacto_invalidos_responden_422_y_socio_inexistente_404(sistema):
    r = sistema.post("/socios", json={"nombre": "Ana", "email": "sin-arroba"})
    assert r.status_code == 422 and r.json()["codigo"] == "DATOS_INVALIDOS"
    r = sistema.get("/socios/no-existe")
    assert r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO"


@pytest.mark.us("US-11", "E1")
def test_contratar_trimestral_vence_exactamente_a_tres_meses_y_cobra_la_tarifa(sistema):
    sid = sistema.socio("Beto")
    r = sistema.post(f"/socios/{sid}/membresia", json={"tipo": "TRIMESTRAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 201
    m = r.json()
    assert m["fecha_inicio"] == "2026-11-09" and m["fecha_vencimiento"] == "2027-02-09"
    assert m["estado"] == "ACTIVA" and "yoga" in m["servicios_incluidos"]
    assert [(c[1], c[2]) for c in sistema.pasarela.cobros] == [(Decimal("1500.00"), "MEMBRESIA_TRIMESTRAL")]
    assert sistema.get(f"/socios/{sid}/membresia").json()["fecha_vencimiento"] == "2027-02-09"


def test_pago_rechazado_no_crea_membresia(sistema):
    sid = sistema.socio("Carla")
    r = sistema.post(f"/socios/{sid}/membresia", json={"tipo": "MENSUAL", "referencia_pago": "FAIL-TARJETA"})
    assert r.status_code == 402 and r.json()["codigo"] == "PAGO_RECHAZADO"
    assert sistema.get(f"/socios/{sid}/membresia").status_code == 404
    assert sistema.pasarela.cobros == []


def test_contratar_dos_veces_se_rechaza_y_se_reembolsa_el_cobro(sistema):
    sid = sistema.con_membresia("Diego", "MENSUAL")
    r = sistema.post(f"/socios/{sid}/membresia", json={"tipo": "ANUAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 409 and r.json()["codigo"] == "MEMBRESIA_EXISTENTE"
    assert len(sistema.pasarela.cobros) == 2 and len(sistema.pasarela.reembolsos) == 1  # compensación


@pytest.mark.us("US-11", "E2")
def test_mejora_de_mensual_a_anual_recalcula_el_vencimiento_desde_fin_de_mes(sistema):
    sid = sistema.con_membresia("Eva", "MENSUAL")
    r = sistema.post(f"/socios/{sid}/membresia/mejora", json={"tipo": "ANUAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 200
    assert r.json()["tipo"] == "ANUAL" and r.json()["fecha_vencimiento"] == "2027-11-30"


def test_mejora_invalida_responde_409(sistema):
    sid = sistema.con_membresia("Fer", "ANUAL")
    r = sistema.post(f"/socios/{sid}/membresia/mejora", json={"tipo": "MENSUAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 409 and r.json()["codigo"] == "MEJORA_INVALIDA"
    assert len(sistema.pasarela.reembolsos) == 1


def test_renovacion_extiende_la_vigencia(sistema):
    sid = sistema.con_membresia("Gus", "MENSUAL")
    r = sistema.post(f"/socios/{sid}/membresia/renovacion", json={"tipo": "TRIMESTRAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 200 and r.json()["fecha_vencimiento"] == "2027-03-09"


def test_renovar_sin_membresia_responde_404(sistema):
    sid = sistema.socio("Hugo")
    r = sistema.post(f"/socios/{sid}/membresia/renovacion", json={"tipo": "MENSUAL", "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 404 and sistema.pasarela.reembolsos != []


def test_la_vista_de_membresia_se_marca_vencida_con_el_paso_del_tiempo(sistema):
    sid = sistema.con_membresia("Ines", "MENSUAL")
    assert sistema.get(f"/socios/{sid}/membresia").json()["estado"] == "ACTIVA"
    sistema.reloj.avanzar(days=40)
    assert sistema.get(f"/socios/{sid}/membresia").json()["estado"] == "VENCIDA"


@pytest.mark.us("US-06", "E1")
@pytest.mark.us("US-06", "E2")
def test_suspension_bloquea_el_acceso_con_motivo_y_la_regularizacion_lo_restaura(sistema):
    sid = sistema.con_membresia("Jorge")
    assert sistema.post(f"/socios/{sid}/suspension", json={"motivo": "Pago pendiente"}).json()["estado"] == "SUSPENDIDA"
    denegado = sistema.post("/accesos", json={"socio_id": sid})
    assert denegado.status_code == 403
    assert denegado.json()["codigo"] == "MEMBRESIA_SUSPENDIDA" and "Pago pendiente" in denegado.json()["mensaje"]
    assert sistema.delete(f"/socios/{sid}/suspension").json()["estado"] == "ACTIVA"
    assert sistema.post("/accesos", json={"socio_id": sid}).status_code == 200


def test_suspender_dos_veces_o_reactivar_activa_responde_409(sistema):
    sid = sistema.con_membresia("Karla")
    assert sistema.delete(f"/socios/{sid}/suspension").status_code == 409
    sistema.post(f"/socios/{sid}/suspension", json={"motivo": "x"})
    assert sistema.post(f"/socios/{sid}/suspension", json={"motivo": "y"}).status_code == 409
    assert sistema.post(f"/socios/{sid}/suspension", json={"motivo": " "}).status_code in (409, 422)
