import pytest

from src.domain.clase_especial import CLASE_FSM, RESERVA_FSM, EstadoClase, EstadoReserva
from src.domain.errors import InvalidTransition
from src.domain.membresia import MEMBRESIA_FSM, EstadoMembresia
from src.domain.pago import PAGO_FSM, EstadoPago
from src.domain.specifications import (
    ClaseCancelada, ContextoAutoridad, ContextoReserva, EsInstructorSuplente, EsInstructorTitular,
    MembresiaNoSuspendida, MembresiaVigente, Specification, puede_gestionar_sesion, puede_reservar,
)
from src.domain.state_machine import StateMachine
from tests.factories import AHORA, clase, membresia


def test_fsm_transicion_valida_e_invalida():
    assert MEMBRESIA_FSM.disparar(EstadoMembresia.ACTIVA, "suspender") == EstadoMembresia.SUSPENDIDA
    with pytest.raises(InvalidTransition):
        MEMBRESIA_FSM.disparar(EstadoMembresia.VENCIDA, "suspender")


def test_fsm_consultas_y_diagrama():
    assert RESERVA_FSM.puede(EstadoReserva.CONFIRMADA, "cancelar")
    assert not RESERVA_FSM.puede(EstadoReserva.NO_SHOW, "cancelar")
    assert RESERVA_FSM.disparadores_desde(EstadoReserva.CONFIRMADA) == [
        "cancelar", "marcar_no_show", "registrar_asistencia"]
    assert "[*] --> PROGRAMADA" in CLASE_FSM.a_mermaid(EstadoClase.PROGRAMADA)
    assert len(PAGO_FSM.transiciones()) == 1
    with pytest.raises(InvalidTransition):
        PAGO_FSM.disparar(EstadoPago.RECHAZADO, "reembolsar")
    assert isinstance(StateMachine("x", {}), StateMachine)


def _ctx(m=None, c=None, socio="socio-1"):
    return ContextoReserva(m or membresia(), c or clase(), socio, AHORA)


def test_specification_and_or_not_componen():
    ok, ctx = MembresiaVigente(), _ctx()
    cancelada = ClaseCancelada()
    assert (ok & ~cancelada).is_satisfied_by(ctx)
    assert (cancelada | ok).is_satisfied_by(ctx)
    assert not (cancelada & ok).is_satisfied_by(ctx)
    assert isinstance(ok & cancelada, Specification)


@pytest.mark.us("US-06", "E1")
def test_explicar_devuelve_motivo_de_cada_regla_fallida():
    m = membresia()
    m.suspender("Adeudo", AHORA)
    fallas = (MembresiaNoSuspendida() & MembresiaVigente()).explicar(_ctx(m=m))
    assert [f.codigo for f in fallas] == ["MEMBRESIA_SUSPENDIDA"]
    c = clase()
    c.cancelar_sesion("inst-1", "Imprevisto", AHORA)
    codigos = [f.codigo for f in puede_reservar().explicar(_ctx(c=c))]
    assert codigos == ["CLASE_CANCELADA"]  # NOT conserva el motivo de la regla interna


def test_or_explica_ambas_fallas_si_ninguna_se_cumple():
    ctx = ContextoAutoridad(clase(), "otro")
    fallas = (EsInstructorTitular() | EsInstructorSuplente()).explicar(ctx)
    assert len(fallas) == 2
    assert puede_gestionar_sesion().explicar(ContextoAutoridad(clase(), "inst-1")) == []
