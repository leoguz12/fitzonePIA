from __future__ import annotations

from .base import AggregateRoot, nuevo_id
from .errors import InvalidData


class Socio(AggregateRoot):
    """Aggregate Root Socio. Invariante: datos de contacto válidos."""

    def __init__(self, id: str, nombre: str, email: str, advertencias: int = 0, no_shows: int = 0) -> None:
        super().__init__()
        if not nombre or not nombre.strip():
            raise InvalidData("El socio requiere un nombre")
        correo = (email or "").strip()
        local, _, dominio = correo.partition("@")
        if not local or "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
            raise InvalidData("El socio requiere un correo de contacto válido")
        self.id = id
        self.nombre = nombre.strip()
        self.email = correo
        self.advertencias = advertencias
        self.no_shows = no_shows

    @classmethod
    def registrar(cls, nombre: str, email: str) -> "Socio":
        return cls(nuevo_id(), nombre, email)

    def registrar_advertencia(self) -> None:
        self.advertencias += 1

    def registrar_no_show(self) -> None:
        self.no_shows += 1
