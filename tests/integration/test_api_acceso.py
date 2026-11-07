import time

import pytest


@pytest.mark.us("US-01", "E1")
@pytest.mark.us("US-14", "E1")
def test_acceso_exitoso_registra_la_entrada(sistema):
    sid = sistema.con_membresia("Ana")
    r = sistema.post("/accesos", json={"socio_id": sid})
    assert r.status_code == 200
    assert r.json()["permitido"] is True and r.json()["alerta"] is None
    historial = sistema.get(f"/socios/{sid}/accesos").json()
    assert len(historial) == 1 and historial[0]["permitido"] is True


@pytest.mark.us("US-01", "E2")
def test_membresia_vencida_arroja_alerta_roja_y_deniega_el_paso(sistema):
    sid = sistema.con_membresia("Beto", "MENSUAL", fecha_inicio="2026-08-01")
    r = sistema.post("/accesos", json={"socio_id": sid})
    assert r.status_code == 403
    assert r.json()["alerta"] == "ROJA" and r.json()["codigo"] == "MEMBRESIA_VENCIDA"
    assert sistema.get(f"/socios/{sid}/membresia").json()["estado"] == "VENCIDA"  # el recálculo se persistió
    historial = sistema.get(f"/socios/{sid}/accesos").json()
    assert historial[0]["permitido"] is False and historial[0]["motivo"] == "MEMBRESIA_VENCIDA"


def test_socio_sin_membresia_no_entra(sistema):
    sid = sistema.socio("Carla")
    r = sistema.post("/accesos", json={"socio_id": sid})
    assert r.status_code == 403 and r.json()["codigo"] == "SIN_MEMBRESIA"


def test_el_ultimo_dia_de_vigencia_entra_con_advertencia(sistema):
    sid = sistema.con_membresia("Diego", "MENSUAL", fecha_inicio="2026-10-09")  # vence 2026-11-09 (hoy)
    r = sistema.post("/accesos", json={"socio_id": sid})
    assert r.status_code == 200 and "justo a tiempo" in r.json()["advertencia"]


def test_acceso_de_socio_inexistente_responde_404(sistema):
    assert sistema.post("/accesos", json={"socio_id": "fantasma"}).status_code == 404
    assert sistema.get("/socios/fantasma/accesos").status_code == 404
    assert sistema.get("/socios/fantasma/notificaciones").status_code == 404


@pytest.mark.us("US-14", "E1")
def test_la_validacion_integral_responde_en_menos_de_2_segundos_y_muestra_las_clases_reservadas(sistema):
    sid = sistema.con_membresia("Ana")
    cid = sistema.clase(nombre="Yoga de hoy")
    sistema.reservar(cid, sid)
    inicio = time.perf_counter()
    r = sistema.post("/accesos", json={"socio_id": sid})
    duracion = time.perf_counter() - inicio
    assert r.status_code == 200 and duracion < 2.0
    assert [x["nombre"] for x in r.json()["reservas_hoy"]] == ["Yoga de hoy"]
    sin_reserva = sistema.con_membresia("Beto")
    assert sistema.post("/accesos", json={"socio_id": sin_reserva}).json()["reservas_hoy"] == []
