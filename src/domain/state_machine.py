"""Máquina de estados genérica.

Las reglas de transición viven en una tabla ``(estado, disparador) -> estado``
declarativa. Así cada agregado delega aquí qué cambios de estado son válidos y
los diagramas de la documentación se generan desde la misma tabla.
"""
from __future__ import annotations

from enum import Enum
from typing import Generic, Mapping, TypeVar

from .errors import InvalidTransition

S = TypeVar("S", bound=Enum)


class StateMachine(Generic[S]):
    def __init__(self, nombre: str, transiciones: Mapping[tuple[S, str], S]) -> None:
        self.nombre = nombre
        self._transiciones: dict[tuple[S, str], S] = dict(transiciones)

    def puede(self, estado: S, disparador: str) -> bool:
        return (estado, disparador) in self._transiciones

    def disparar(self, estado: S, disparador: str) -> S:
        try:
            return self._transiciones[(estado, disparador)]
        except KeyError:
            raise InvalidTransition(
                f"{self.nombre}: no se puede '{disparador}' desde el estado {estado.value}"
            ) from None

    def disparadores_desde(self, estado: S) -> list[str]:
        return sorted(d for (e, d) in self._transiciones if e == estado)

    def transiciones(self) -> list[tuple[S, str, S]]:
        return [(e, d, destino) for (e, d), destino in self._transiciones.items()]

    def a_mermaid(self, inicial: S) -> str:
        lineas = ["stateDiagram-v2", f"    [*] --> {inicial.value}"]
        for origen, disparador, destino in self.transiciones():
            lineas.append(f"    {origen.value} --> {destino.value}: {disparador}")
        return "\n".join(lineas)
