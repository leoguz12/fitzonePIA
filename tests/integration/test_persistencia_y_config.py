"""Persistencia (repositorios + Unit of Work), configuración y arranque."""
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import OperationalError

from src.api.container import build_container
from src.api.main import create_app
from src.domain.clase_especial import ClaseEspecial
from src.domain.socio import Socio
from src.infrastructure import db as db_mod
from src.infrastructure.config import Settings, normalizar_url
from src.infrastructure.orm import Base, SocioORM
from src.infrastructure.payment_gateway import PasarelaSimulada
from src.infrastructure.seed import sembrar_datos_demo
from tests.factories import AHORA


def test_unit_of_work_commit_persiste(sistema):
    socio = Socio.registrar("Ana", "ana@fitzone.mx")
    with sistema.container.deps.uow_factory() as uow:
        uow.socios.add(socio)
        uow.commit()
    with sistema.container.deps.uow_factory() as uow:
        assert uow.socios.get(socio.id).nombre == "Ana"
        assert uow.socios.get("otro") is None


def test_unit_of_work_rollback_si_hay_excepcion_no_persiste_nada(sistema):
    socio = Socio.registrar("Beto", "beto@fitzone.mx")
    with pytest.raises(RuntimeError):
        with sistema.container.deps.uow_factory() as uow:
            uow.socios.add(socio)
            uow.session.flush()          # ya está en la transacción...
            raise RuntimeError("falla a mitad del proceso")
    with sistema.container.session_factory() as s:
        assert s.get(SocioORM, socio.id) is None  # ...pero se revirtió


def test_unit_of_work_rollback_explicito(sistema):
    socio = Socio.registrar("Carla", "carla@fitzone.mx")
    with sistema.container.deps.uow_factory() as uow:
        uow.socios.add(socio)
        uow.rollback()
    with sistema.container.session_factory() as s:
        assert s.get(SocioORM, socio.id) is None


def test_el_repositorio_de_clases_conserva_reservas_y_el_orden_fifo_de_la_lista(sistema):
    inst = sistema.instructor()
    clase = ClaseEspecial.programar("Yoga", inst, AHORA + timedelta(hours=8), 60, 1, "yoga", Decimal("150.00"))
    socios = [Socio.registrar(f"S{i}", f"s{i}@fitzone.mx") for i in range(4)]
    with sistema.container.deps.uow_factory() as uow:
        for s in socios:
            uow.socios.add(s)
        uow.commit()
        uow.clases.add(clase)
        uow.commit()
    with sistema.container.deps.uow_factory() as uow:
        c = uow.clases.get(clase.id, bloquear=True)
        c.reservar(socios[0].id, AHORA)
        for s in socios[1:]:
            c.unirse_lista_espera(s.id, AHORA)
        uow.clases.save(c)
        uow.commit()
    with sistema.container.deps.uow_factory() as uow:
        c = uow.clases.get(clase.id)
        assert c.ocupados == 1 and c.lista_espera.socios == [s.id for s in socios[1:]]
        c.abandonar_lista_espera(socios[2].id)
        uow.clases.save(c)
        uow.commit()
    with sistema.container.deps.uow_factory() as uow:
        assert uow.clases.get(clase.id).lista_espera.socios == [socios[1].id, socios[3].id]
        assert uow.clases.get("no-existe") is None


def test_repositorio_de_pagos_y_membresias_devuelven_none_si_no_existen(sistema):
    with sistema.container.deps.uow_factory() as uow:
        assert uow.pagos.get("x") is None
        assert uow.membresias.get_por_socio("x") is None
        assert uow.instructores.get("x") is None


def test_health(sistema):
    assert sistema.get("/health").json() == {"status": "ok", "entorno": "development",
                                             "hora_servidor": "2026-11-09T10:00:00"}


def test_swagger_y_openapi_estan_activos(sistema):
    assert sistema.get("/docs").status_code == 200
    spec = sistema.get("/openapi.json").json()
    assert spec["info"]["title"] == "FitZone API" and "/clases/{clase_id}/reservas" in spec["paths"]


def test_datos_demo_se_siembran_una_sola_vez():
    settings = Settings(database_url="sqlite://", seed_demo_data=True)
    container = build_container(settings, reloj=lambda: AHORA, pasarela=PasarelaSimulada())
    app = create_app(settings, container)
    assert sembrar_datos_demo(container.deps, container.session_factory) == {}  # ya estaba sembrado
    with container.session_factory() as s:
        assert s.query(SocioORM).count() == 5
    from fastapi.testclient import TestClient
    cliente = TestClient(app)
    assert len(cliente.get("/clases").json()) == 3
    carla = [s for s in [cliente.get(f"/socios/{i}").json() for i in _ids(container)] if s["nombre"].startswith("Carla")][0]
    assert cliente.post("/accesos", json={"socio_id": carla["id"]}).json()["codigo"] == "MEMBRESIA_SUSPENDIDA"


def _ids(container):
    with container.session_factory() as s:
        return [r.id for r in s.query(SocioORM).all()]


def test_settings_desde_el_entorno():
    s = Settings.from_env({"DATABASE_URL": "postgres://u:p@host/db", "TOLERANCIA_MINUTOS": "15",
                           "LIMITE_CANCELACION_HORAS": "4", "TARIFA_ANUAL": "4800", "SEED_DEMO_DATA": "true",
                           "APP_ENV": "production"})
    assert s.database_url == "postgresql+psycopg://u:p@host/db"
    assert (s.tolerancia_minutos, s.limite_cancelacion_horas, s.app_env, s.seed_demo_data) == (15, 4, "production", True)
    reglas = s.reglas()
    assert reglas.tolerancia == timedelta(minutes=15) and reglas.limite_cancelacion == timedelta(hours=4)
    assert reglas.tarifas[list(reglas.tarifas)[2]] == Decimal("4800")
    assert Settings.from_env({}).seed_demo_data is False and Settings.from_env({}).tolerancia_minutos == 10


def test_normalizar_url():
    assert normalizar_url("postgres://a") == "postgresql+psycopg://a"
    assert normalizar_url("postgresql://a") == "postgresql+psycopg://a"
    assert normalizar_url("postgresql+psycopg://a") == "postgresql+psycopg://a"
    assert normalizar_url("sqlite://") == "sqlite://"


def test_crear_tablas_reintenta_mientras_la_bd_arranca(monkeypatch):
    llamadas = {"n": 0}

    def inestable(*a, **k):
        llamadas["n"] += 1
        if llamadas["n"] < 3:
            raise OperationalError("conexión", {}, Exception("db aún no lista"))

    monkeypatch.setattr(Base.metadata, "create_all", inestable)
    monkeypatch.setattr(db_mod.time, "sleep", lambda s: None)
    db_mod.crear_tablas(object(), intentos=5)
    assert llamadas["n"] == 3
    llamadas["n"] = -100
    with pytest.raises(OperationalError):
        db_mod.crear_tablas(object(), intentos=2)


def test_pasarela_simulada_rechaza_referencias_fail_y_registra_reembolsos():
    p = PasarelaSimulada()
    assert p.cobrar(Decimal("10"), "fail-x", "c").aprobado is False
    ok = p.cobrar(Decimal("10"), "TARJETA", "c")
    assert ok.aprobado and ok.referencia_externa.startswith("SIM-")
    p.reembolsar(ok.referencia_externa)
    assert p.reembolsos == [ok.referencia_externa]
