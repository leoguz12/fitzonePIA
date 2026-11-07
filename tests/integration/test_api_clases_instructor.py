from datetime import date, timedelta

import pytest


def test_programar_clase_valida_instructor_y_datos(sistema):
    cuerpo = {"nombre": "Yoga", "instructor_id": "fantasma", "inicio": "2026-11-10T07:00:00",
              "duracion_min": 60, "capacidad": 10, "servicio_requerido": "yoga", "precio_extra": "100.00"}
    assert sistema.post("/clases", json=cuerpo).status_code == 404
    cuerpo["instructor_id"] = sistema.instructor()
    assert sistema.post("/clases", json={**cuerpo, "capacidad": 0}).status_code == 422
    assert sistema.post("/clases", json={**cuerpo, "precio_extra": "0"}).status_code == 422
    r = sistema.post("/clases", json=cuerpo)
    assert r.status_code == 201 and r.json()["capacidad"] == 10 and r.json()["estado"] == "PROGRAMADA"


@pytest.mark.us("US-08", "E1")
def test_instructor_consulta_horario_y_aforo_de_sus_clases_del_dia(sistema):
    inst = sistema.instructor("Laura")
    cid = sistema.clase(capacidad=5, instructor_id=inst)
    for n in ("Ana", "Beto"):
        sistema.reservar(cid, sistema.con_membresia(n))
    hoy = sistema.reloj().date().isoformat()
    r = sistema.get(f"/instructores/{inst}/clases", params={"fecha": hoy})
    assert r.status_code == 200 and len(r.json()) == 1
    clase = r.json()[0]
    assert (clase["capacidad"], clase["inscritos"]) == (5, 2) and clase["resumen"] == "2 inscritos de 5"
    otro_dia = (sistema.reloj().date() + timedelta(days=3)).isoformat()
    assert sistema.get(f"/instructores/{inst}/clases", params={"fecha": otro_dia}).json() == []


@pytest.mark.us("US-08", "E2")
def test_clase_sin_reservas_indica_cero_inscritos(sistema):
    inst = sistema.instructor("Laura")
    sistema.clase(instructor_id=inst)
    r = sistema.get(f"/instructores/{inst}/clases", params={"fecha": sistema.reloj().date().isoformat()})
    assert r.json()[0]["inscritos"] == 0 and r.json()[0]["resumen"].startswith("0 inscritos")


def test_aforo_de_clase_inexistente_responde_404(sistema):
    assert sistema.get("/clases/fantasma/aforo").status_code == 404


@pytest.mark.us("US-09", "E1")
def test_instructor_cancela_la_sesion_se_notifica_a_inscritos_y_se_liberan_cupos(sistema):
    inst = sistema.instructor("Laura")
    cid = sistema.clase(capacidad=1, instructor_id=inst)
    inscrito, en_espera = sistema.con_membresia("Inscrito"), sistema.con_membresia("En Espera")
    sistema.reservar(cid, inscrito); sistema.reservar(cid, en_espera)
    r = sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": inst, "motivo": "Instructor enfermo"})
    assert r.status_code == 200 and r.json() == {"cancelada": True, "socios_notificados": 2}
    for s in (inscrito, en_espera):
        assert "Clase cancelada" in sistema.notificaciones(s)
    a = sistema.aforo(cid)
    assert a["estado"] == "CANCELADA" and a["inscritos"] == 0 and a["en_lista_espera"] == 0
    assert sistema.get("/clases").json() == []  # ya no aparece en el catálogo
    assert sistema.reservar(cid, sistema.con_membresia("Tarde")).status_code == 409


def test_solo_el_instructor_de_la_clase_puede_cancelar_y_una_sola_vez(sistema):
    inst = sistema.instructor("Laura")
    cid = sistema.clase(instructor_id=inst)
    r = sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": "intruso", "motivo": "x"})
    assert r.status_code == 403 and r.json()["codigo"] == "INSTRUCTOR_NO_AUTORIZADO"
    assert sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": inst, "motivo": " "}).status_code == 422
    assert sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": inst, "motivo": "x"}).status_code == 200
    assert sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": inst, "motivo": "x"}).status_code == 409


@pytest.mark.us("US-09", "E2")
def test_el_administrador_asigna_suplente_la_clase_sigue_activa_y_se_notifica(sistema):
    titular, suplente = sistema.instructor("Titular"), sistema.instructor("Suplente")
    cid = sistema.clase(instructor_id=titular)
    socio = sistema.con_membresia("Ana")
    sistema.reservar(cid, socio)
    r = sistema.put(f"/clases/{cid}/instructor-suplente", json={"instructor_id": suplente})
    assert r.status_code == 200 and r.json()["instructor_suplente_id"] == suplente
    assert sistema.aforo(cid)["estado"] == "PROGRAMADA"
    assert "Cambio de instructor" in sistema.notificaciones(socio)
    hoy = sistema.reloj().date().isoformat()
    assert len(sistema.get(f"/instructores/{suplente}/clases", params={"fecha": hoy}).json()) == 1
    ok = sistema.post(f"/clases/{cid}/cancelacion", json={"instructor_id": suplente, "motivo": "titular ausente"})
    assert ok.status_code == 200  # el suplente también tiene autoridad


def test_suplente_invalido(sistema):
    titular = sistema.instructor("Titular")
    cid = sistema.clase(instructor_id=titular)
    assert sistema.put(f"/clases/{cid}/instructor-suplente", json={"instructor_id": "fantasma"}).status_code == 404
    assert sistema.put(f"/clases/{cid}/instructor-suplente", json={"instructor_id": titular}).status_code == 409


def test_finalizar_la_clase_cierra_pendientes_como_no_show(sistema):
    cid = sistema.clase(horas=1)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    assert sistema.post(f"/clases/{cid}/finalizacion").status_code == 409  # aún no termina
    sistema.reloj.avanzar(hours=3)
    r = sistema.post(f"/clases/{cid}/finalizacion")
    assert r.status_code == 200 and r.json()["estado"] == "FINALIZADA"
    assert sistema.socio_datos(sid)["no_shows"] == 1
    assert sistema.post(f"/clases/{cid}/finalizacion").status_code == 409
