from __future__ import annotations

from uuid import uuid4

from .events import DomainEvent


def nuevo_id() -> str:
    return str(uuid4())


class AggregateRoot:
    """Raíz de agregado: único punto de entrada para modificar su estado.

    Acumula eventos de dominio que la capa de aplicación publica después de
    confirmar la transacción.
    """

    def __init__(self) -> None:
        self._eventos: list[DomainEvent] = []

    def _registrar(self, evento: DomainEvent) -> None:
        self._eventos.append(evento)

    def extraer_eventos(self) -> list[DomainEvent]:
        eventos, self._eventos = self._eventos, []
        return eventos
