"""Aggregate Root Membresía: motor de permisos del socio (CU-01, US-01/06/11)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from .base import AggregateRoot, nuevo_id
from .errors import BusinessRuleViolation, InvalidData
from .events import (
    AccesoDenegado,
    AccesoPermitido,
    MembresiaContratada,
    MembresiaMejorada,
    MembresiaReactivada,
    MembresiaRenovada,
    MembresiaSuspendida,
)
from .specifications import ContextoAcceso, Falla, acceso_permitido
from .state_machine import StateMachine
from .value_objects import PlanContratado, TipoPlan, Vigencia, add_months, fin_de_mes


class EstadoMembresia(str, Enum):
    ACTIVA = "ACTIVA"
    SUSPENDIDA = "SUSPENDIDA"
    VENCIDA = "VENCIDA"


MEMBRESIA_FSM: StateMachine[EstadoMembresia] = StateMachine(
    "Membresia",
    {
        (EstadoMembresia.ACTIVA, "suspender"): EstadoMembresia.SUSPENDIDA,
        (EstadoMembresia.SUSPENDIDA, "reactivar"): EstadoMembresia.ACTIVA,
        (EstadoMembresia.ACTIVA, "vencer"): EstadoMembresia.VENCIDA,
        (EstadoMembresia.VENCIDA, "renovar"): EstadoMembresia.ACTIVA,
        (EstadoMembresia.ACTIVA, "renovar"): EstadoMembresia.ACTIVA,
        (EstadoMembresia.ACTIVA, "mejorar_plan"): EstadoMembresia.ACTIVA,
    },
)


@dataclass(frozen=True)
class ResultadoAcceso:
    permitido: bool
    codigo: str | None
    mensaje: str
    advertencia: str | None = None
    fallas: tuple[Falla, ...] = ()


class Membresia(AggregateRoot):
    def __init__(
        self,
        id: str,
        socio_id: str,
        plan: PlanContratado,
        vigencia: Vigencia,
        estado: EstadoMembresia = EstadoMembresia.ACTIVA,
        motivo_suspension: str | None = None,
    ) -> None:
        super().__init__()
        self.id = id
        self.socio_id = socio_id
        self.plan = plan
        self.vigencia = vigencia
        self.estado = estado
        self.motivo_suspension = motivo_suspension

    @classmethod
    def nueva(cls, socio_id: str, tipo: TipoPlan, inicio: date, ahora: datetime) -> "Membresia":
        m = cls(nuevo_id(), socio_id, PlanContratado.de_tipo(tipo), Vigencia.desde(inicio, tipo))
        m._registrar(
            MembresiaContratada(
                socio_id=socio_id,
                tipo=tipo.value,
                vencimiento=m.vigencia.fecha_vencimiento,
                ocurrido_en=ahora,
            )
        )
        return m

    @property
    def suspendida(self) -> bool:
        return self.estado == EstadoMembresia.SUSPENDIDA

    def refrescar_estado(self, ahora: datetime) -> None:
        """Recalcula el estado según la fecha del sistema (ACTIVA -> VENCIDA)."""
        if self.estado == EstadoMembresia.ACTIVA and self.vigencia.vencida_en(ahora.date()):
            self.estado = MEMBRESIA_FSM.disparar(self.estado, "vencer")

    def validar_acceso(self, ahora: datetime) -> ResultadoAcceso:
        self.refrescar_estado(ahora)
        fallas = acceso_permitido().explicar(ContextoAcceso(self, ahora.date()))
        if fallas:
            principal = fallas[0]
            mensaje = principal.mensaje
            if principal.codigo == "MEMBRESIA_SUSPENDIDA" and self.motivo_suspension:
                mensaje = f"{mensaje} Motivo: {self.motivo_suspension}"
            self._registrar(
                AccesoDenegado(socio_id=self.socio_id, motivo=principal.codigo, ocurrido_en=ahora)
            )
            return ResultadoAcceso(False, principal.codigo, mensaje, None, tuple(fallas))
        advertencia = None
        if self.vigencia.fecha_vencimiento == ahora.date():
            advertencia = "Tu membresía vence hoy: ¡entraste justo a tiempo!"
        self._registrar(
            AccesoPermitido(socio_id=self.socio_id, advertencia=advertencia, ocurrido_en=ahora)
        )
        return ResultadoAcceso(True, None, "Acceso permitido", advertencia)

    def suspender(self, motivo: str, ahora: datetime) -> None:
        if not motivo or not motivo.strip():
            raise InvalidData("Se requiere un motivo para suspender la membresía")
        self.estado = MEMBRESIA_FSM.disparar(self.estado, "suspender")
        self.motivo_suspension = motivo.strip()
        self._registrar(MembresiaSuspendida(socio_id=self.socio_id, motivo=self.motivo_suspension, ocurrido_en=ahora))

    def reactivar(self, ahora: datetime) -> None:
        """US-06 E2: recepción regulariza; se restauran privilegios si sigue vigente."""
        self.estado = MEMBRESIA_FSM.disparar(self.estado, "reactivar")
        self.motivo_suspension = None
        self.refrescar_estado(ahora)
        self._registrar(MembresiaReactivada(socio_id=self.socio_id, ocurrido_en=ahora))

    def renovar(self, tipo: TipoPlan, ahora: datetime) -> None:
        self.refrescar_estado(ahora)
        hoy = ahora.date()
        if self.estado == EstadoMembresia.ACTIVA and self.vigencia.vigente_en(hoy):
            inicio = self.vigencia.fecha_inicio
            fin = add_months(self.vigencia.fecha_vencimiento, tipo.meses)
        else:
            inicio, fin = hoy, add_months(hoy, tipo.meses)
        self.estado = MEMBRESIA_FSM.disparar(self.estado, "renovar")
        self.plan = PlanContratado.de_tipo(tipo)
        self.vigencia = Vigencia(inicio, fin)
        self._registrar(MembresiaRenovada(socio_id=self.socio_id, tipo=tipo.value, vencimiento=fin, ocurrido_en=ahora))

    def mejorar_plan(self, nuevo: TipoPlan, ahora: datetime) -> None:
        """US-11 E2: el nuevo vencimiento se cuenta desde el FIN DEL MES ACTUAL."""
        self.refrescar_estado(ahora)
        if nuevo.nivel <= self.plan.tipo.nivel:
            raise BusinessRuleViolation(
                "Solo se puede mejorar a un plan de mayor nivel", "MEJORA_INVALIDA"
            )
        self.estado = MEMBRESIA_FSM.disparar(self.estado, "mejorar_plan")
        fin = add_months(fin_de_mes(ahora.date()), nuevo.meses)
        self.plan = PlanContratado.de_tipo(nuevo)
        self.vigencia = Vigencia(self.vigencia.fecha_inicio, fin)
        self._registrar(MembresiaMejorada(socio_id=self.socio_id, tipo=nuevo.value, vencimiento=fin, ocurrido_en=ahora))
