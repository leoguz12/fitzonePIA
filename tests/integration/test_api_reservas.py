from decimal import Decimal

import pytest

from src.application import reserva_service
from src.infrastructure.orm import PagoORM, ReservaORM


@pytest.mark.us("US-02", "E1")
def test_reserva_confirmada_asigna_lugar_y_reduce_el_cupo(sistema):
    cid = sistema.clase(capacidad=3)
    sid = sistema.con_membresia("Ana")
    r = sistema.reservar(cid, sid)
    assert r.status_code == 201 and r.json()["resultado"] == "CONFIRMADA"
    a = sistema.aforo(cid)
    assert a["inscritos"] == 1 and a["cupos_disponibles"] == 2
    assert "Reserva confirmada" in sistema.notificaciones(sid)


@pytest.mark.us("US-02", "E2")
def test_clase_fuera_del_plan_se_bloquea_y_notifica_pago_adicional(sistema):
    cid = sistema.clase(servicio="yoga", precio="150.00")
    sid = sistema.con_membresia("Beto", "MENSUAL")  # el plan mensual no incluye yoga
    r = sistema.reservar(cid, sid)
    assert r.status_code == 402
    assert r.json()["codigo"] == "REQUIERE_PAGO_ADICIONAL" and r.json()["monto_adicional"] == "150.00"
    assert sistema.aforo(cid)["inscritos"] == 0


@pytest.mark.us("US-03", "E1")
def test_clase_llena_agrega_al_final_de_la_lista_de_espera(sistema):
    cid = sistema.clase(capacidad=1)
    a, b, c = (sistema.con_membresia(n) for n in ("Ana", "Beto", "Carla"))
    assert sistema.reservar(cid, a).status_code == 201
    rb, rc = sistema.reservar(cid, b), sistema.reservar(cid, c)
    assert rb.status_code == 202 and rb.json()["posicion"] == 1
    assert rc.status_code == 202 and rc.json()["posicion"] == 2
    assert sistema.aforo(cid)["en_lista_espera"] == 2
    assert "Lista de espera" in sistema.notificaciones(b)


@pytest.mark.us("US-03", "E2")
def test_abandonar_la_lista_de_espera_recorre_a_los_siguientes(sistema):
    cid = sistema.clase(capacidad=1)
    a, b, c = (sistema.con_membresia(n) for n in ("Ana", "Beto", "Carla"))
    for s in (a, b, c):
        sistema.reservar(cid, s)
    assert sistema.delete(f"/clases/{cid}/lista-espera/{b}").json() == {"retirado": True}
    assert sistema.aforo(cid)["en_lista_espera"] == 1
    assert sistema.delete(f"/clases/{cid}/lista-espera/{b}").status_code == 409
    # Carla ahora es la primera: al liberarse el lugar, ella entra
    reserva_a = sistema.container.session_factory().query(ReservaORM).filter_by(socio_id=a).one().id
    assert sistema.delete(f"/clases/{cid}/reservas/{reserva_a}").status_code == 200
    assert "¡Lugar asignado!" in sistema.notificaciones(c)


def _reserva_id(sistema, socio_id):
    with sistema.container.session_factory() as s:
        return s.query(ReservaORM).filter_by(socio_id=socio_id).one().id


@pytest.mark.us("US-04", "E1")
def test_cancelacion_a_tiempo_libera_el_lugar_sin_advertencia(sistema):
    cid = sistema.clase(capacidad=2, horas=8)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    r = sistema.delete(f"/clases/{cid}/reservas/{_reserva_id(sistema, sid)}")
    assert r.status_code == 200 and r.json()["tardia"] is False
    assert sistema.aforo(cid)["cupos_disponibles"] == 2
    assert sistema.socio_datos(sid)["advertencias"] == 0


@pytest.mark.us("US-04", "E2")
def test_cancelacion_tardia_libera_el_lugar_y_registra_advertencia_en_el_perfil(sistema):
    cid = sistema.clase(capacidad=2, horas=1)  # menos de 2 h para iniciar
    sid = sistema.con_membresia("Beto")
    sistema.reservar(cid, sid)
    r = sistema.delete(f"/clases/{cid}/reservas/{_reserva_id(sistema, sid)}")
    assert r.json()["tardia"] is True
    assert sistema.aforo(cid)["cupos_disponibles"] == 2
    assert sistema.socio_datos(sid)["advertencias"] == 1


def test_cancelar_dos_veces_o_reserva_inexistente(sistema):
    cid = sistema.clase()
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    rid = _reserva_id(sistema, sid)
    assert sistema.delete(f"/clases/{cid}/reservas/{rid}").status_code == 200
    assert sistema.delete(f"/clases/{cid}/reservas/{rid}").status_code == 409
    assert sistema.delete(f"/clases/{cid}/reservas/fantasma").status_code == 404


@pytest.mark.us("US-05", "E1")
def test_al_liberarse_un_lugar_se_asigna_automaticamente_al_primero_de_la_lista(sistema):
    cid = sistema.clase(capacidad=1)
    a, b, c = (sistema.con_membresia(n) for n in ("Ana", "Beto", "Carla"))
    sistema.reservar(cid, a); sistema.reservar(cid, b); sistema.reservar(cid, c)
    sistema.delete(f"/clases/{cid}/reservas/{_reserva_id(sistema, a)}")
    aforo = sistema.aforo(cid)
    assert aforo["inscritos"] == 1 and aforo["en_lista_espera"] == 1
    assert "¡Lugar asignado!" in sistema.notificaciones(b)       # Beto era el primero
    assert "¡Lugar asignado!" not in sistema.notificaciones(c)


@pytest.mark.us("US-05", "E2")
def test_sin_lista_de_espera_el_lugar_vuelve_al_catalogo_general(sistema):
    cid = sistema.clase(capacidad=1)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    assert sistema.get("/clases").json()[0]["cupos_disponibles"] == 0
    sistema.delete(f"/clases/{cid}/reservas/{_reserva_id(sistema, sid)}")
    catalogo = sistema.get("/clases").json()
    assert catalogo[0]["clase_id"] == cid and catalogo[0]["cupos_disponibles"] == 1


def test_el_socio_de_la_lista_que_ya_no_es_elegible_se_descarta(sistema):
    cid = sistema.clase(capacidad=1)
    a, b, c = (sistema.con_membresia(n) for n in ("Ana", "Beto", "Carla"))
    sistema.reservar(cid, a); sistema.reservar(cid, b); sistema.reservar(cid, c)
    sistema.post(f"/socios/{b}/suspension", json={"motivo": "Adeudo"})  # Beto se suspende mientras espera
    sistema.delete(f"/clases/{cid}/reservas/{_reserva_id(sistema, a)}")
    assert "¡Lugar asignado!" not in sistema.notificaciones(b)
    assert "¡Lugar asignado!" in sistema.notificaciones(c)


def test_reservas_denegadas_por_membresia_duplicado_o_clase_inexistente(sistema):
    cid = sistema.clase()
    vencida = sistema.con_membresia("Vencida", "MENSUAL", fecha_inicio="2026-08-01")
    r = sistema.reservar(cid, vencida)
    assert r.status_code == 403 and "MEMBRESIA_VENCIDA" in r.json()["motivos"]
    suspendida = sistema.con_membresia("Suspendida")
    sistema.post(f"/socios/{suspendida}/suspension", json={"motivo": "x"})
    assert sistema.reservar(cid, suspendida).status_code == 403
    sin_membresia = sistema.socio("Sin Plan")
    assert sistema.reservar(cid, sin_membresia).json()["motivos"] == ["SIN_MEMBRESIA"]
    ok = sistema.con_membresia("Ok")
    sistema.reservar(cid, ok)
    r = sistema.reservar(cid, ok)
    assert r.status_code == 409 and r.json()["codigo"] == "RESERVA_DUPLICADA"
    assert sistema.reservar("fantasma", ok).status_code == 404
    assert sistema.reservar(cid, "fantasma").status_code == 404


@pytest.mark.us("US-12", "E1")
def test_pago_exitoso_en_mostrador_registra_el_cobro_y_habilita_el_cupo(sistema):
    cid = sistema.clase(servicio="yoga", precio="150.00")
    sid = sistema.con_membresia("Ana", "MENSUAL")
    r = sistema.post(f"/clases/{cid}/pagos-fuera-de-plan", json={"socio_id": sid, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 201 and r.json()["resultado"] == "CONFIRMADA"
    assert sistema.aforo(cid)["inscritos"] == 1
    assert sistema.pasarela.cobros[-1][1] == Decimal("150.00")
    with sistema.container.session_factory() as s:
        assert s.query(PagoORM).filter(PagoORM.concepto.like("CLASE_FUERA_DE_PLAN%")).one().estado == "APROBADO"
        assert s.query(ReservaORM).filter_by(socio_id=sid).one().pago_id is not None


@pytest.mark.us("US-12", "E2")
def test_pago_rechazado_mantiene_la_restriccion(sistema):
    cid = sistema.clase(servicio="yoga")
    sid = sistema.con_membresia("Beto", "MENSUAL")
    r = sistema.post(f"/clases/{cid}/pagos-fuera-de-plan", json={"socio_id": sid, "referencia_pago": "FAIL-TARJETA"})
    assert r.status_code == 402 and r.json()["codigo"] == "PAGO_RECHAZADO"
    assert sistema.aforo(cid)["inscritos"] == 0
    with sistema.container.session_factory() as s:
        assert s.query(PagoORM).filter(PagoORM.concepto.like("CLASE_FUERA_DE_PLAN%")).one().estado == "RECHAZADO"


def test_no_se_cobra_si_la_clase_esta_llena_o_el_plan_ya_la_incluye(sistema):
    cid = sistema.clase(capacidad=1, servicio="yoga")
    anual = sistema.con_membresia("Ana", "ANUAL")
    mensual = sistema.con_membresia("Beto", "MENSUAL")
    r = sistema.post(f"/clases/{cid}/pagos-fuera-de-plan", json={"socio_id": anual, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 409 and r.json()["codigo"] == "PLAN_YA_INCLUYE_CLASE"
    sistema.reservar(cid, anual)
    r = sistema.post(f"/clases/{cid}/pagos-fuera-de-plan", json={"socio_id": mensual, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 409 and r.json()["codigo"] == "CLASE_LLENA"
    clases_cobradas = [c for c in sistema.pasarela.cobros if c[2].startswith("CLASE")]
    assert clases_cobradas == []  # nunca se cobró


def test_si_falla_la_operacion_despues_del_cobro_se_reembolsa_y_no_queda_reserva(sistema, monkeypatch):
    """Riesgo del reporte U5: cobrar sin registrar la reserva. Debe compensarse con un reembolso."""
    cid = sistema.clase(servicio="yoga")
    sid = sistema.con_membresia("Ana", "MENSUAL")

    def falla(*args, **kwargs):
        raise RuntimeError("falló la BD después del cobro")

    monkeypatch.setattr(reserva_service, "solicitar_lugar", falla)
    cliente_sin_reraise = type(sistema.client)(sistema.client.app, raise_server_exceptions=False)
    r = cliente_sin_reraise.post(f"/clases/{cid}/pagos-fuera-de-plan", json={"socio_id": sid, "referencia_pago": "TARJETA-OK"})
    assert r.status_code == 500
    assert len(sistema.pasarela.reembolsos) == 1
    with sistema.container.session_factory() as s:
        assert s.query(ReservaORM).filter_by(socio_id=sid).count() == 0
        assert s.query(PagoORM).filter(PagoORM.concepto.like("CLASE_FUERA_DE_PLAN%")).one().estado == "REEMBOLSADO"


@pytest.mark.us("US-15", "E1")
def test_recepcion_ve_el_aforo_exacto_y_registra_manualmente_a_quien_llega_sin_reserva(sistema):
    cid = sistema.clase(capacidad=3, horas=1)
    reservado = sistema.con_membresia("Ana")
    sistema.reservar(cid, reservado)
    a = sistema.aforo(cid)
    assert (a["capacidad"], a["inscritos"], a["cupos_disponibles"]) == (3, 1, 2)
    presencial = sistema.con_membresia("Llega Sin Reserva")
    assert sistema.reservar(cid, presencial).status_code == 201
    assert sistema.aforo(cid)["cupos_disponibles"] == 1


@pytest.mark.us("US-15", "E2")
def test_clase_saturada_nunca_sobrepasa_la_capacidad_maxima(sistema):
    cid = sistema.clase(capacidad=2, horas=1)
    socios = [sistema.con_membresia(f"Socio {i}") for i in range(4)]
    codigos = [sistema.reservar(cid, s).status_code for s in socios]
    assert codigos == [201, 201, 202, 202]
    a = sistema.aforo(cid)
    assert a["inscritos"] == 2 <= a["capacidad"] and a["cupos_disponibles"] == 0
