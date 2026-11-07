"""Puertos de persistencia (Repository Pattern).

El dominio solo conoce estas interfaces; las implementaciones viven en
``infrastructure`` (Dependency Inversion Principle). Cada interfaz es pequeña y
específica (Interface Segregation Principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .clase_especial import ClaseEspecial
from .entrenamiento import PaqueteEntrenamiento
from .instructor import Instructor
from .membresia import Membresia
from .pago import Pago
from .socio import Socio


class SocioRepository(ABC):
    @abstractmethod
    def add(self, socio: Socio) -> None: ...

    @abstractmethod
    def get(self, socio_id: str) -> Optional[Socio]: ...

    @abstractmethod
    def save(self, socio: Socio) -> None: ...


class MembresiaRepository(ABC):
    @abstractmethod
    def add(self, membresia: Membresia) -> None: ...

    @abstractmethod
    def get_por_socio(self, socio_id: str) -> Optional[Membresia]: ...

    @abstractmethod
    def save(self, membresia: Membresia) -> None: ...


class InstructorRepository(ABC):
    @abstractmethod
    def add(self, instructor: Instructor) -> None: ...

    @abstractmethod
    def get(self, instructor_id: str) -> Optional[Instructor]: ...


class ClaseRepository(ABC):
    @abstractmethod
    def add(self, clase: ClaseEspecial) -> None: ...

    @abstractmethod
    def get(self, clase_id: str, bloquear: bool = False) -> Optional[ClaseEspecial]:
        """``bloquear=True`` toma un bloqueo de fila (evita sobre-reservar el último cupo)."""

    @abstractmethod
    def save(self, clase: ClaseEspecial) -> None: ...


class PagoRepository(ABC):
    @abstractmethod
    def add(self, pago: Pago) -> None: ...

    @abstractmethod
    def get(self, pago_id: str) -> Optional[Pago]: ...


class EntrenamientoRepository(ABC):
    @abstractmethod
    def add(self, paquete: PaqueteEntrenamiento) -> None: ...

    @abstractmethod
    def get(self, paquete_id: str) -> Optional[PaqueteEntrenamiento]: ...
