from datetime import timedelta

import pytest


@pytest.mark.us("US-10", "E1")
def test_reporte_de_demanda_muestra_tasa_de_ocupacion_y_lugares_vacios_por_clase(sistema):
    c1 = sistema.clase(capacidad=4, nombre="Yoga Lleno-ish")
    c2 = sistema.clase(capacidad=10, nombre="Yoga Vacío")
    for n in ("Ana", "Beto", "Carla"):
        sistema.reservar(c1, sistema.con_membresia(n))
    hoy = sistema.reloj().date()
    r = sistema.get("/reportes/demanda", params={"desde": hoy.isoformat(), "hasta": hoy.isoformat()})
    assert r.status_code == 200
    por_clase = {c["clase_id"]: c for c in r.json()["clases"]}
    assert por_clase[c1]["tasa_ocupacion"] == 75.0 and por_clase[c1]["lugares_vacios"] == 1
    assert por_clase[c2]["tasa_ocupacion"] == 0.0 and por_clase[c2]["lugares_vacios"] == 10
    resumen = r.json()["resumen"]
    assert resumen["total_clases"] == 2 and resumen["tasa_ocupacion_promedio"] == 37.5
    assert resumen["lugares_vacios_total"] == 11


@pytest.mark.us("US-10", "E2")
def test_el_filtro_de_fechas_ajusta_las_metricas_exclusivamente_al_periodo(sistema):
    sistema.clase(capacidad=4, horas=8)                 # hoy
    sistema.clase(capacidad=4, horas=24 * 40)           # dentro de ~40 días
    hoy = sistema.reloj().date()
    r = sistema.get("/reportes/demanda", params={"desde": hoy.isoformat(), "hasta": (hoy + timedelta(days=7)).isoformat()})
    assert r.json()["resumen"]["total_clases"] == 1
    r = sistema.get("/reportes/demanda", params={"desde": (hoy + timedelta(days=30)).isoformat(),
                                                   "hasta": (hoy + timedelta(days=60)).isoformat()})
    assert r.json()["resumen"]["total_clases"] == 1
    r = sistema.get("/reportes/demanda", params={"desde": "2020-01-01", "hasta": "2020-01-31"})
    assert r.json()["resumen"] == {"total_clases": 0, "clases_canceladas": 0, "tasa_ocupacion_promedio": 0.0,
                                   "lugares_vacios_total": 0, "tasa_no_show": 0.0}


def test_rango_de_fechas_invalido_responde_422(sistema):
    r = sistema.get("/reportes/demanda", params={"desde": "2026-12-01", "hasta": "2026-11-01"})
    assert r.status_code == 422 and r.json()["codigo"] == "DATOS_INVALIDOS"


def test_el_reporte_calcula_la_tasa_de_no_show_y_excluye_clases_canceladas(sistema):
    inst = sistema.instructor("Laura")
    cid = sistema.clase(capacidad=4, horas=1, instructor_id=inst)
    asiste, falta = sistema.con_membresia("Asiste"), sistema.con_membresia("Falta")
    sistema.reservar(cid, asiste); sistema.reservar(cid, falta)
    sistema.reloj.avanzar(hours=1, minutes=2)
    sistema.post(f"/clases/{cid}/asistencias", json={"socio_id": asiste})
    sistema.reloj.avanzar(minutes=20)
    sistema.post(f"/clases/{cid}/no-shows")
    cancelada = sistema.clase(capacidad=4, horas=6, instructor_id=inst)
    sistema.post(f"/clases/{cancelada}/cancelacion", json={"instructor_id": inst, "motivo": "x"})
    hoy = sistema.reloj().date()
    resumen = sistema.get("/reportes/demanda", params={"desde": hoy.isoformat(), "hasta": hoy.isoformat()}).json()["resumen"]
    assert resumen["tasa_no_show"] == 50.0  # 1 asistencia, 1 no-show
    assert resumen["total_clases"] == 2 and resumen["clases_canceladas"] == 1
