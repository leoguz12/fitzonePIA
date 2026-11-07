import pytest

from src.infrastructure.orm import ReservaORM


def _preparar(sistema, capacidad=2, horas=1):
    cid = sistema.clase(capacidad=capacidad, horas=horas)
    return cid


@pytest.mark.us("US-07", "E1")
def test_pasada_la_tolerancia_la_reserva_sin_asistencia_se_etiqueta_no_show(sistema):
    cid = _preparar(sistema)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    sistema.reloj.avanzar(hours=1, minutes=11)  # la clase inició hace 11 min; tolerancia = 10
    r = sistema.post(f"/clases/{cid}/no-shows")
    assert r.status_code == 200 and r.json() == {"no_shows": [sid], "total": 1}
    assert sistema.socio_datos(sid)["no_shows"] == 1
    assert "No-show registrado" in sistema.notificaciones(sid)
    with sistema.container.session_factory() as s:
        assert s.query(ReservaORM).filter_by(socio_id=sid).one().estado == "NO_SHOW"
    assert sistema.aforo(cid)["cupos_disponibles"] == 2  # el lugar se liberó


def test_dentro_de_la_tolerancia_todavia_no_hay_no_show(sistema):
    cid = _preparar(sistema)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    sistema.reloj.avanzar(hours=1, minutes=5)
    assert sistema.post(f"/clases/{cid}/no-shows").json()["total"] == 0
    assert sistema.socio_datos(sid)["no_shows"] == 0


def test_el_no_show_libera_el_lugar_y_se_asigna_al_primero_de_la_lista(sistema):
    """Diagrama de secuencia 2: etiqueta No-Show -> libera -> asigna al 1ro en lista -> notifica."""
    cid = _preparar(sistema, capacidad=1)
    ausente, espera = sistema.con_membresia("Ausente"), sistema.con_membresia("En Espera")
    sistema.reservar(cid, ausente)
    assert sistema.reservar(cid, espera).status_code == 202
    sistema.reloj.avanzar(hours=1, minutes=11)
    sistema.post(f"/clases/{cid}/no-shows")
    assert "¡Lugar asignado!" in sistema.notificaciones(espera)
    a = sistema.aforo(cid)
    assert a["inscritos"] == 1 and a["en_lista_espera"] == 0 and a["no_shows"] == 1


@pytest.mark.us("US-07", "E2")
def test_llegar_dentro_de_la_tolerancia_valida_la_asistencia_y_no_genera_no_show(sistema):
    cid = _preparar(sistema)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    sistema.reloj.avanzar(hours=1, minutes=10)  # justo en el límite de tolerancia
    r = sistema.post(f"/clases/{cid}/asistencias", json={"socio_id": sid})
    assert r.status_code == 200 and r.json()["resultado"] == "ASISTENCIA_REGISTRADA"
    sistema.reloj.avanzar(minutes=30)
    assert sistema.post(f"/clases/{cid}/no-shows").json()["total"] == 0
    assert sistema.socio_datos(sid)["no_shows"] == 0
    assert sistema.aforo(cid)["asistencias"] == 1


def test_llegar_fuera_de_la_tolerancia_es_no_show_y_su_lugar_se_reasigna(sistema):
    cid = _preparar(sistema)
    sid = sistema.con_membresia("Ana")
    sistema.reservar(cid, sid)
    sistema.reloj.avanzar(hours=1, minutes=11)
    r = sistema.post(f"/clases/{cid}/asistencias", json={"socio_id": sid})
    assert r.json()["resultado"] == "NO_SHOW" and "tarde" in r.json()["mensaje"]
    assert sistema.socio_datos(sid)["no_shows"] == 1


def test_asistencia_sin_reserva_o_clase_inexistente(sistema):
    cid = _preparar(sistema)
    sid = sistema.con_membresia("Ana")
    r = sistema.post(f"/clases/{cid}/asistencias", json={"socio_id": sid})
    assert r.status_code == 409 and r.json()["codigo"] == "SIN_RESERVA"
    assert sistema.post("/clases/fantasma/asistencias", json={"socio_id": sid}).status_code == 404
