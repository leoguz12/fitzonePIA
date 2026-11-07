"""Suscriptores de eventos de dominio (cada uno con su propia transacción)."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..domain import events as ev
from .context import Dependencias
from .lista_espera_service import ListaEsperaAppService
from .ports import Notificacion, RegistroAcceso


def registrar_handlers(deps: Dependencias) -> None:
    bus = deps.bus
    lista_espera = ListaEsperaAppService(deps)

    def notificar(socios: Iterable[str], asunto: str, mensaje: str, cuando: datetime) -> None:
        with deps.uow_factory() as uow:
            for socio_id in socios:
                uow.notificaciones.add(Notificacion(socio_id, asunto, mensaje, cuando))
            uow.commit()

    # --- Lista de espera (US-05): LugarLiberado -> asignar vacante ----------
    bus.suscribir(ev.LugarLiberado, lambda e: lista_espera.asignar_vacante(e.clase_id))

    # --- Sanciones (US-04 E2, US-07 E1) -------------------------------------
    def al_no_show(e: ev.NoShowRegistrado) -> None:
        with deps.uow_factory() as uow:
            socio = uow.socios.get(e.socio_id)
            if socio is not None:
                socio.registrar_no_show()
                uow.socios.save(socio)
                uow.commit()
        notificar([e.socio_id], "No-show registrado", "No asististe a tu clase reservada. Tu lugar fue liberado.", e.ocurrido_en)

    def al_cancelacion_tardia(e: ev.CancelacionTardiaRegistrada) -> None:
        with deps.uow_factory() as uow:
            socio = uow.socios.get(e.socio_id)
            if socio is not None:
                socio.registrar_advertencia()
                uow.socios.save(socio)
                uow.commit()

    bus.suscribir(ev.NoShowRegistrado, al_no_show)
    bus.suscribir(ev.CancelacionTardiaRegistrada, al_cancelacion_tardia)

    # --- Notificaciones al socio ---------------------------------------------
    bus.suscribir(ev.ReservaConfirmada, lambda e: notificar(
        [e.socio_id], "Reserva confirmada", "¡Tu lugar está confirmado! Te esperamos en clase.", e.ocurrido_en))
    bus.suscribir(ev.SocioAgregadoAListaEspera, lambda e: notificar(
        [e.socio_id], "Lista de espera",
        f"Clase llena. Te hemos agregado a la lista de espera (posición {e.posicion}).", e.ocurrido_en))
    bus.suscribir(ev.SocioAsignadoDesdeEspera, lambda e: notificar(
        [e.socio_id], "¡Lugar asignado!", "Se liberó un lugar y te fue asignado automáticamente.", e.ocurrido_en))
    bus.suscribir(ev.ClaseCancelada, lambda e: notificar(
        e.socios_afectados, "Clase cancelada",
        f"Tu clase fue cancelada por el instructor. Motivo: {e.motivo}. Tu cupo fue liberado.", e.ocurrido_en))
    bus.suscribir(ev.InstructorSuplenteAsignado, lambda e: notificar(
        e.socios_afectados, "Cambio de instructor",
        "Tu clase sigue en pie pero cambió el instructor (suplente asignado).", e.ocurrido_en))

    # --- Historial de accesos (US-01 / reportes de intentos denegados) --------
    def registrar_acceso(socio_id, permitido, motivo, advertencia, cuando) -> None:
        with deps.uow_factory() as uow:
            uow.accesos.add(RegistroAcceso(socio_id, permitido, motivo, advertencia, cuando))
            uow.commit()

    bus.suscribir(ev.AccesoPermitido, lambda e: registrar_acceso(e.socio_id, True, None, e.advertencia, e.ocurrido_en))
    bus.suscribir(ev.AccesoDenegado, lambda e: registrar_acceso(e.socio_id, False, e.motivo, None, e.ocurrido_en))
