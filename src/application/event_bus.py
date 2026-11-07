from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable

from ..domain.events import DomainEvent


class EventBus:
    """Bus de eventos en proceso: desacopla "algo ocurrió" de "qué hacer al respecto"."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def suscribir(self, tipo: type, handler: Callable) -> None:
        self._handlers[tipo].append(handler)

    def publicar(self, eventos: Iterable[DomainEvent]) -> None:
        for evento in eventos:
            for handler in self._handlers.get(type(evento), []):
                handler(evento)
