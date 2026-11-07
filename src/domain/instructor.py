from __future__ import annotations

from .base import nuevo_id
from .errors import InvalidData


class Instructor:
    """Entidad: empleado que imparte clases (visualiza aforo y cancela sesión)."""

    def __init__(self, id: str, nombre: str) -> None:
        if not nombre or not nombre.strip():
            raise InvalidData("El instructor requiere un nombre")
        self.id = id
        self.nombre = nombre.strip()

    @classmethod
    def registrar(cls, nombre: str) -> "Instructor":
        return cls(nuevo_id(), nombre)
