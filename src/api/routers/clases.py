from fastapi import APIRouter, Depends, Response

from ..container import Container
from ..deps import get_container
from ..schemas import CancelarSesionIn, ClaseIn, PagoClaseIn, SocioRefIn, SuplenteIn

router = APIRouter(prefix="/clases", tags=["Clases especiales y reservas"])


@router.post("", status_code=201, summary="Programar una clase especial")
def programar(d: ClaseIn, c: Container = Depends(get_container)):
    clase = c.clases.programar(d.nombre, d.instructor_id, d.inicio, d.duracion_min, d.capacidad,
                               d.servicio_requerido, d.precio_extra)
    return c.consultas.consultar_aforo(clase.id)


@router.get("", summary="US-05 E2 / US-15: catálogo de clases programadas con cupos disponibles")
def catalogo(c: Container = Depends(get_container)):
    return c.consultas.catalogo_clases()


@router.get("/{clase_id}/aforo", summary="US-08 / US-15: capacidad, inscritos y lista de espera")
def aforo(clase_id: str, c: Container = Depends(get_container)):
    return c.consultas.consultar_aforo(clase_id)


@router.post("/{clase_id}/reservas", status_code=201,
             summary="US-02 / US-03: reservar (201) o entrar a lista de espera (202); 402 si el plan no incluye la clase")
def reservar(clase_id: str, d: SocioRefIn, response: Response, c: Container = Depends(get_container)):
    r = c.reservas.reservar(clase_id, d.socio_id)
    if r.tipo == "CONFIRMADA":
        return {"resultado": "CONFIRMADA", "reserva_id": r.reserva.id, "posicion": None,
                "mensaje": "¡Tu lugar está confirmado! Te esperamos en clase."}
    response.status_code = 202
    return {"resultado": "LISTA_ESPERA", "reserva_id": None, "posicion": r.posicion,
            "mensaje": f"Clase llena. Te hemos agregado a la lista de espera (posición {r.posicion})."}


@router.post("/{clase_id}/pagos-fuera-de-plan", status_code=201,
             summary="US-12: cobrar en mostrador una clase fuera de plan y habilitar el cupo")
def pagar_fuera_de_plan(clase_id: str, d: PagoClaseIn, c: Container = Depends(get_container)):
    r = c.reservas.reservar_con_pago(clase_id, d.socio_id, d.referencia_pago)
    return {"resultado": "CONFIRMADA", "reserva_id": r.reserva.id, "mensaje": "Cobro registrado y lugar habilitado."}


@router.delete("/{clase_id}/reservas/{reserva_id}", summary="US-04: cancelar reserva (tardía = advertencia)")
def cancelar_reserva(clase_id: str, reserva_id: str, c: Container = Depends(get_container)):
    tardia = c.reservas.cancelar_reserva(clase_id, reserva_id)
    return {"cancelada": True, "tardia": tardia,
            "mensaje": "Lugar liberado con advertencia en tu perfil." if tardia else "Lugar liberado."}


@router.delete("/{clase_id}/lista-espera/{socio_id}", summary="US-03 E2: abandonar la lista de espera")
def abandonar_lista(clase_id: str, socio_id: str, c: Container = Depends(get_container)):
    c.reservas.abandonar_lista_espera(clase_id, socio_id)
    return {"retirado": True}


@router.post("/{clase_id}/asistencias", summary="US-07 E2: registrar asistencia (dentro de tolerancia) o No-Show")
def asistencia(clase_id: str, d: SocioRefIn, c: Container = Depends(get_container)):
    r = c.asistencia.registrar_asistencia(clase_id, d.socio_id)
    msg = ("Asistencia registrada correctamente." if r.value == "ASISTENCIA_REGISTRADA"
           else "Llegaste tarde. Tu lugar fue reasignado.")
    return {"resultado": r.value, "mensaje": msg}


@router.post("/{clase_id}/no-shows", summary="US-07 E1: procesar No-Shows al terminar la tolerancia")
def procesar_no_shows(clase_id: str, c: Container = Depends(get_container)):
    socios = c.asistencia.procesar_no_shows(clase_id)
    return {"no_shows": socios, "total": len(socios)}


@router.post("/{clase_id}/cancelacion", summary="US-09 E1: el instructor cancela la sesión y se notifica a los inscritos")
def cancelar_sesion(clase_id: str, d: CancelarSesionIn, c: Container = Depends(get_container)):
    afectados = c.clases.cancelar_sesion(clase_id, d.instructor_id, d.motivo)
    return {"cancelada": True, "socios_notificados": len(afectados)}


@router.put("/{clase_id}/instructor-suplente", summary="US-09 E2: el administrador asigna instructor suplente")
def suplente(clase_id: str, d: SuplenteIn, c: Container = Depends(get_container)):
    clase = c.clases.asignar_suplente(clase_id, d.instructor_id)
    return {"clase_id": clase.id, "instructor_suplente_id": clase.instructor_suplente_id}


@router.post("/{clase_id}/finalizacion", summary="Finalizar la clase (pendientes pasan a No-Show)")
def finalizar(clase_id: str, c: Container = Depends(get_container)):
    clase = c.clases.finalizar(clase_id)
    return {"clase_id": clase.id, "estado": clase.estado.value}
