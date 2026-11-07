"""Fixtures de integración: API real + BD real (SQLite en memoria por defecto,
PostgreSQL si se define TEST_DATABASE_URL, como hace docker compose)."""
import os
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.container import build_container
from src.api.main import create_app
from src.infrastructure.config import Settings
from src.infrastructure.orm import Base
from src.infrastructure.payment_gateway import PasarelaSimulada
from tests.factories import AHORA


class RelojFalso:
    def __init__(self, ahora):
        self.ahora = ahora

    def __call__(self):
        return self.ahora

    def avanzar(self, **kwargs):
        self.ahora += timedelta(**kwargs)


class Sistema:
    """Atajos para armar escenarios a través de la API pública."""

    def __init__(self, client, reloj, pasarela, container):
        self.client, self.reloj, self.pasarela, self.container = client, reloj, pasarela, container
        self._instructor = None

    def post(self, *a, **k): return self.client.post(*a, **k)
    def get(self, *a, **k): return self.client.get(*a, **k)
    def delete(self, *a, **k): return self.client.delete(*a, **k)
    def put(self, *a, **k): return self.client.put(*a, **k)

    def socio(self, nombre="Socio Demo", email=None):
        email = email or f"{nombre.lower().replace(' ', '.')}@fitzone.mx"
        r = self.post("/socios", json={"nombre": nombre, "email": email})
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def con_membresia(self, nombre="Socio Demo", tipo="ANUAL", fecha_inicio=None):
        socio_id = self.socio(nombre)
        body = {"tipo": tipo, "referencia_pago": "TARJETA-OK"}
        if fecha_inicio:
            body["fecha_inicio"] = fecha_inicio
        r = self.post(f"/socios/{socio_id}/membresia", json=body)
        assert r.status_code == 201, r.text
        return socio_id

    def instructor(self, nombre="Laura Pérez"):
        r = self.post("/instructores", json={"nombre": nombre})
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def clase(self, capacidad=2, servicio="yoga", horas=8, precio="150.00", instructor_id=None, nombre="Yoga Vespertino"):
        instructor_id = instructor_id or self.instructor()
        inicio = (self.reloj() + timedelta(hours=horas)).isoformat()
        r = self.post("/clases", json={
            "nombre": nombre, "instructor_id": instructor_id, "inicio": inicio, "duracion_min": 60,
            "capacidad": capacidad, "servicio_requerido": servicio, "precio_extra": precio})
        assert r.status_code == 201, r.text
        return r.json()["clase_id"]

    def reservar(self, clase_id, socio_id):
        return self.post(f"/clases/{clase_id}/reservas", json={"socio_id": socio_id})

    def aforo(self, clase_id):
        return self.get(f"/clases/{clase_id}/aforo").json()

    def notificaciones(self, socio_id):
        return [n["asunto"] for n in self.get(f"/socios/{socio_id}/notificaciones").json()]

    def socio_datos(self, socio_id):
        return self.get(f"/socios/{socio_id}").json()


@pytest.fixture
def sistema():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    reloj, pasarela = RelojFalso(AHORA), PasarelaSimulada()
    settings = Settings(database_url=url)
    container = build_container(settings, reloj=reloj, pasarela=pasarela)
    Base.metadata.drop_all(container.engine)
    app = create_app(settings, container)
    yield Sistema(TestClient(app), reloj, pasarela, container)
    Base.metadata.drop_all(container.engine)
    container.engine.dispose()


DEC = Decimal
