"""Aggregate Root ClaseEspecial (CU-02, CU-03, US-02/03/04/05/07/09).

Controla estrictamente el aforo físico: es la única clase autorizada para crear
Reservas o añadir socios a la ListaEspera. Invariante: cupos disponibles >= 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable, Optional

from .base import AggregateRoot, nuevo_id
from .errors import BusinessRuleViolation, Forbidden, InvalidData, NotFound
from .events import (
    AsistenciaRegistrada,
    CancelacionTardiaRegistrada,
    CapacidadAlcanzada,
    ClaseCancelada,
    InstructorSuplenteAsignado,
    LugarLiberado,
    NoShowRegistrado,
    ReservaConfirmada,
    SocioAgregadoAListaEspera,
    SocioAsignadoDesdeEspera,
)
from .specifications import (
    CancelacionATiempo,
    ContextoAsistencia,
    ContextoAutoridad,
    ContextoCancelacion,
    DentroDeTolerancia,
    puede_gestionar_sesion,
)
from .state_machine import StateMachine
from .value_objects import CapacidadMaxima


class EstadoClase(str, Enum):
    PROGRAMADA = "PROGRAMADA"
    EN_CURSO = "EN_CURSO"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class EstadoReserva(str, Enum):
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    ASISTIDA = "ASISTIDA"
    NO_SHOW = "NO_SHOW"


class ResultadoAsistencia(str, Enum):
    ASISTENCIA_REGISTRADA = "ASISTENCIA_REGISTRADA"
    NO_SHOW = "NO_SHOW"


CLASE_FSM: StateMachine[EstadoClase] = StateMachine(
    "ClaseEspecial",
    {
        (EstadoClase.PROGRAMADA, "iniciar"): EstadoClase.EN_CURSO,
        (EstadoClase.EN_CURSO, "finalizar"): EstadoClase.FINALIZADA,
        (EstadoClase.PROGRAMADA, "cancelar"): EstadoClase.CANCELADA,
    },
)

RESERVA_FSM: StateMachine[EstadoReserva] = StateMachine(
    "Reserva",
    {
        (EstadoReserva.CONFIRMADA, "cancelar"): EstadoReserva.CANCELADA,
        (EstadoReserva.CONFIRMADA, "registrar_asistencia"): EstadoReserva.ASISTIDA,
        (EstadoReserva.CONFIRMADA, "marcar_no_show"): EstadoReserva.NO_SHOW,
    },
)

OCUPAN_LUGAR = (EstadoReserva.CONFIRMADA, EstadoReserva.ASISTIDA)


class Reserva:
    """Entidad interna del agregado: su ciclo de vida depende de la clase."""

    def __init__(
        self,
        id: str,
        socio_id: str,
        creada_en: datetime,
        estado: EstadoReserva = EstadoReserva.CONFIRMADA,
        pago_id: Optional[str] = None,
        cancelada_tarde: bool = False,
    ) -> None:
        self.id = id
        self.socio_id = socio_id
        self.creada_en = creada_en
        self.estado = estado
        self.pago_id = pago_id
        self.cancelada_tarde = cancelada_tarde

    @property
    def ocupa_lugar(self) -> bool:
        return self.estado in OCUPAN_LUGAR

    def cancelar(self, tarde: bool) -> None:
        self.estado = RESERVA_FSM.disparar(self.estado, "cancelar")
        self.cancelada_tarde = tarde

    def registrar_asistencia(self) -> None:
        self.estado = RESERVA_FSM.disparar(self.estado, "registrar_asistencia")

    def marcar_no_show(self) -> None:
        self.estado = RESERVA_FSM.disparar(self.estado, "marcar_no_show")


@dataclass(frozen=True)
class EntradaListaEspera:
    socio_id: str
    agregado_en: datetime


class ListaEspera:
    """Entidad secuencial FIFO. La posición es el orden en la cola (1, 2, 3...)."""

    def __init__(self, entradas: Iterable[EntradaListaEspera] = ()) -> None:
        self._entradas: list[EntradaListaEspera] = list(entradas)

    def __len__(self) -> int:
        return len(self._entradas)

    @property
    def entradas(self) -> tuple[EntradaListaEspera, ...]:
        return tuple(self._entradas)

    @property
    def socios(self) -> list[str]:
        return [e.socio_id for e in self._entradas]

    def posicion_de(self, socio_id: str) -> Optional[int]:
        for i, e in enumerate(self._entradas, start=1):
            if e.socio_id == socio_id:
                return i
        return None

    def agregar(self, socio_id: str, ahora: datetime) -> int:
        if self.posicion_de(socio_id) is not None:
            raise BusinessRuleViolation("El socio ya está en la lista de espera", "YA_EN_LISTA_ESPERA")
        self._entradas.append(EntradaListaEspera(socio_id, ahora))
        return len(self._entradas)

    def retirar(self, socio_id: str) -> bool:
        """Quita al socio; los lugares subsecuentes se recorren automáticamente."""
        for i, e in enumerate(self._entradas):
            if e.socio_id == socio_id:
                del self._entradas[i]
                return True
        return False

    def extraer_primero(self) -> Optional[EntradaListaEspera]:
        return self._entradas.pop(0) if self._entradas else None

    def vaciar(self) -> list[str]:
        socios = self.socios
        self._entradas.clear()
        return socios


class ClaseEspecial(AggregateRoot):
    def __init__(
        self,
        id: str,
        nombre: str,
        instructor_id: str,
        inicio: datetime,
        duracion_min: int,
        capacidad: CapacidadMaxima,
        servicio_requerido: str,
        precio_extra: Decimal,
        estado: EstadoClase = EstadoClase.PROGRAMADA,
        reservas: Optional[Iterable[Reserva]] = None,
        lista_espera: Optional[ListaEspera] = None,
        instructor_suplente_id: Optional[str] = None,
        motivo_cancelacion: Optional[str] = None,
    ) -> None:
        super().__init__()
        if not nombre or not nombre.strip():
            raise InvalidData("La clase requiere un nombre")
        if not servicio_requerido or not servicio_requerido.strip():
            raise InvalidData("La clase requiere el servicio que debe incluir el plan")
        if duracion_min <= 0:
            raise InvalidData("La duración debe ser mayor a cero")
        if Decimal(precio_extra) <= 0:
            raise InvalidData("El precio para clases fuera de plan debe ser mayor a cero")
        self.id = id
        self.nombre = nombre.strip()
        self.instructor_id = instructor_id
        self.inicio = inicio
        self.duracion_min = duracion_min
        self.capacidad = capacidad
        self.servicio_requerido = servicio_requerido.strip().lower()
        self.precio_extra = Decimal(precio_extra)
        self.estado = estado
        self._reservas: list[Reserva] = list(reservas or [])
        self.lista_espera = lista_espera or ListaEspera()
        self.instructor_suplente_id = instructor_suplente_id
        self.motivo_cancelacion = motivo_cancelacion

    @classmethod
    def programar(
        cls,
        nombre: str,
        instructor_id: str,
        inicio: datetime,
        duracion_min: int,
        capacidad: int,
        servicio_requerido: str,
        precio_extra: Decimal,
    ) -> "ClaseEspecial":
        return cls(
            nuevo_id(), nombre, instructor_id, inicio, duracion_min,
            CapacidadMaxima(capacidad), servicio_requerido, precio_extra,
        )

    # --- consultas ---------------------------------------------------------
    @property
    def reservas(self) -> tuple[Reserva, ...]:
        return tuple(self._reservas)

    @property
    def fin(self) -> datetime:
        return self.inicio + timedelta(minutes=self.duracion_min)

    @property
    def cancelada(self) -> bool:
        return self.estado == EstadoClase.CANCELADA

    @property
    def ocupados(self) -> int:
        return sum(1 for r in self._reservas if r.ocupa_lugar)

    @property
    def cupos_disponibles(self) -> int:
        return self.capacidad.limite - self.ocupados

    def reserva_activa_de(self, socio_id: str) -> Optional[Reserva]:
        for r in self._reservas:
            if r.socio_id == socio_id and r.ocupa_lugar:
                return r
        return None

    def tiene_lugar(self, socio_id: str) -> bool:
        return self.reserva_activa_de(socio_id) is not None or self.lista_espera.posicion_de(socio_id) is not None

    def buscar_reserva(self, reserva_id: str) -> Reserva:
        for r in self._reservas:
            if r.id == reserva_id:
                return r
        raise NotFound("La reserva no existe en esta clase")

    # --- comandos ------------------------------------------------------------
    def reservar(self, socio_id: str, ahora: datetime, pago_id: Optional[str] = None) -> Reserva:
        if self.estado != EstadoClase.PROGRAMADA:
            raise BusinessRuleViolation("La clase no admite reservas", "CLASE_NO_DISPONIBLE")
        if self.tiene_lugar(socio_id):
            raise BusinessRuleViolation("El socio ya tiene un lugar en esta clase", "RESERVA_DUPLICADA")
        if self.cupos_disponibles <= 0:  # invariante: nunca exceder la capacidad
            raise BusinessRuleViolation("Se excedería la capacidad máxima", "CAPACIDAD_EXCEDIDA")
        reserva = Reserva(nuevo_id(), socio_id, ahora, pago_id=pago_id)
        self._reservas.append(reserva)
        self._registrar(ReservaConfirmada(clase_id=self.id, socio_id=socio_id, reserva_id=reserva.id, ocurrido_en=ahora))
        return reserva

    def unirse_lista_espera(self, socio_id: str, ahora: datetime) -> int:
        if self.estado != EstadoClase.PROGRAMADA:
            raise BusinessRuleViolation("La clase no admite reservas", "CLASE_NO_DISPONIBLE")
        if self.tiene_lugar(socio_id):
            raise BusinessRuleViolation("El socio ya tiene un lugar en esta clase", "RESERVA_DUPLICADA")
        if self.cupos_disponibles > 0:
            raise BusinessRuleViolation("La clase aún tiene lugares: reserva directamente", "CLASE_CON_CUPO")
        posicion = self.lista_espera.agregar(socio_id, ahora)
        self._registrar(CapacidadAlcanzada(clase_id=self.id, ocurrido_en=ahora))
        self._registrar(SocioAgregadoAListaEspera(clase_id=self.id, socio_id=socio_id, posicion=posicion, ocurrido_en=ahora))
        return posicion

    def abandonar_lista_espera(self, socio_id: str) -> None:
        if not self.lista_espera.retirar(socio_id):
            raise BusinessRuleViolation("El socio no está en la lista de espera", "NO_EN_LISTA_ESPERA")

    def cancelar_reserva(self, reserva_id: str, ahora: datetime, limite: timedelta) -> bool:
        """Devuelve True si la cancelación fue tardía (genera advertencia)."""
        reserva = self.buscar_reserva(reserva_id)
        if ahora >= self.inicio:
            raise BusinessRuleViolation("La clase ya inició", "CLASE_YA_INICIADA")
        a_tiempo = CancelacionATiempo().is_satisfied_by(ContextoCancelacion(self, ahora, limite))
        reserva.cancelar(tarde=not a_tiempo)
        self._registrar(LugarLiberado(clase_id=self.id, reserva_id=reserva.id, socio_id=reserva.socio_id, ocurrido_en=ahora))
        if not a_tiempo:
            self._registrar(CancelacionTardiaRegistrada(clase_id=self.id, socio_id=reserva.socio_id, ocurrido_en=ahora))
        return not a_tiempo

    def asignar_desde_lista_espera(
        self, ahora: datetime, es_elegible: Callable[[str], bool]
    ) -> list[Reserva]:
        """US-05: asigna los lugares libres al primero de la cola (FIFO)."""
        asignadas: list[Reserva] = []
        if self.estado not in (EstadoClase.PROGRAMADA, EstadoClase.EN_CURSO):
            return asignadas
        while self.cupos_disponibles > 0 and len(self.lista_espera) > 0:
            entrada = self.lista_espera.extraer_primero()
            if entrada is None or not es_elegible(entrada.socio_id):
                continue  # el socio ya no cumple las reglas: se descarta de la cola
            reserva = Reserva(nuevo_id(), entrada.socio_id, ahora)
            self._reservas.append(reserva)
            self._registrar(SocioAsignadoDesdeEspera(clase_id=self.id, socio_id=entrada.socio_id, reserva_id=reserva.id, ocurrido_en=ahora))
            asignadas.append(reserva)
        return asignadas

    def _marcar_no_show(self, reserva: Reserva, ahora: datetime, liberar: bool = True) -> None:
        reserva.marcar_no_show()
        self._registrar(NoShowRegistrado(clase_id=self.id, socio_id=reserva.socio_id, reserva_id=reserva.id, ocurrido_en=ahora))
        if liberar:
            self._registrar(LugarLiberado(clase_id=self.id, reserva_id=reserva.id, socio_id=reserva.socio_id, ocurrido_en=ahora))

    def registrar_asistencia(self, socio_id: str, ahora: datetime, tolerancia: timedelta) -> ResultadoAsistencia:
        """US-07 E2: dentro de tolerancia se valida; fuera de ella es No-Show."""
        if self.estado in (EstadoClase.CANCELADA, EstadoClase.FINALIZADA):
            raise BusinessRuleViolation("La clase no está disponible", "CLASE_NO_DISPONIBLE")
        reserva = next(
            (r for r in self._reservas if r.socio_id == socio_id and r.estado == EstadoReserva.CONFIRMADA), None
        )
        if reserva is None:
            raise BusinessRuleViolation("El socio no tiene una reserva confirmada", "SIN_RESERVA")
        if DentroDeTolerancia().is_satisfied_by(ContextoAsistencia(self, ahora, tolerancia)):
            reserva.registrar_asistencia()
            self._registrar(AsistenciaRegistrada(clase_id=self.id, socio_id=socio_id, ocurrido_en=ahora))
            return ResultadoAsistencia.ASISTENCIA_REGISTRADA
        self._marcar_no_show(reserva, ahora)
        return ResultadoAsistencia.NO_SHOW

    def procesar_no_shows(self, ahora: datetime, tolerancia: timedelta) -> list[Reserva]:
        """US-07 E1: al terminar la tolerancia, las reservas sin asistencia son No-Show."""
        if self.estado in (EstadoClase.CANCELADA, EstadoClase.FINALIZADA):
            return []
        if ahora <= self.inicio + tolerancia:
            return []
        if self.estado == EstadoClase.PROGRAMADA:
            self.estado = CLASE_FSM.disparar(self.estado, "iniciar")
        pendientes = [r for r in self._reservas if r.estado == EstadoReserva.CONFIRMADA]
        for r in pendientes:
            self._marcar_no_show(r, ahora)
        return pendientes

    def cancelar_sesion(self, instructor_id: str, motivo: str, ahora: datetime) -> tuple[str, ...]:
        """US-09 E1: cancela la sesión, libera cupos y avisa a todos los afectados."""
        if not puede_gestionar_sesion().is_satisfied_by(ContextoAutoridad(self, instructor_id)):
            raise Forbidden("Solo el instructor titular o su suplente puede cancelar la sesión", "INSTRUCTOR_NO_AUTORIZADO")
        if not motivo or not motivo.strip():
            raise InvalidData("Se requiere un motivo para cancelar la sesión")
        self.estado = CLASE_FSM.disparar(self.estado, "cancelar")
        confirmadas = [r for r in self._reservas if r.estado == EstadoReserva.CONFIRMADA]
        afectados = tuple([r.socio_id for r in confirmadas] + self.lista_espera.vaciar())
        for r in confirmadas:
            r.cancelar(tarde=False)
        self.motivo_cancelacion = motivo.strip()
        self._registrar(ClaseCancelada(clase_id=self.id, socios_afectados=afectados, motivo=self.motivo_cancelacion, ocurrido_en=ahora))
        return afectados

    def asignar_suplente(self, nuevo_instructor_id: str, ahora: datetime) -> None:
        """US-09 E2: la clase sigue activa y se notifica el cambio de instructor."""
        if self.estado != EstadoClase.PROGRAMADA:
            raise BusinessRuleViolation("Solo una clase programada admite suplente", "CLASE_NO_DISPONIBLE")
        if nuevo_instructor_id == self.instructor_id:
            raise BusinessRuleViolation("El suplente debe ser distinto del titular", "SUPLENTE_INVALIDO")
        self.instructor_suplente_id = nuevo_instructor_id
        afectados = tuple(r.socio_id for r in self._reservas if r.estado == EstadoReserva.CONFIRMADA)
        self._registrar(InstructorSuplenteAsignado(clase_id=self.id, instructor_id=nuevo_instructor_id, socios_afectados=afectados, ocurrido_en=ahora))

    def finalizar(self, ahora: datetime) -> None:
        if ahora < self.fin:
            raise BusinessRuleViolation("La clase aún no termina", "CLASE_NO_HA_TERMINADO")
        if self.estado == EstadoClase.PROGRAMADA:
            self.estado = CLASE_FSM.disparar(self.estado, "iniciar")
        self.estado = CLASE_FSM.disparar(self.estado, "finalizar")
        for r in [r for r in self._reservas if r.estado == EstadoReserva.CONFIRMADA]:
            self._marcar_no_show(r, ahora, liberar=False)
