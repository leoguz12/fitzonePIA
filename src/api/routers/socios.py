from fastapi import APIRouter, Depends

from ..container import Container
from ..deps import get_container
from ..schemas import (
    ContratarIn, EntrenamientoIn, MembresiaOut, PlanIn, SocioIn, SocioOut, SuspensionIn, membresia_out, socio_out,
)

router = APIRouter(prefix="/socios", tags=["Socios y membresías"])


@router.post("", response_model=SocioOut, status_code=201, summary="Registrar socio")
def registrar_socio(datos: SocioIn, c: Container = Depends(get_container)):
    return socio_out(c.socios.registrar(datos.nombre, datos.email))


@router.get("/{socio_id}", response_model=SocioOut, summary="Consultar socio (incluye advertencias y no-shows)")
def obtener_socio(socio_id: str, c: Container = Depends(get_container)):
    return socio_out(c.socios.obtener(socio_id))


@router.post("/{socio_id}/membresia", response_model=MembresiaOut, status_code=201,
             summary="US-11 E1: contratar membresía (cobra la tarifa del plan)")
def contratar(socio_id: str, datos: ContratarIn, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.contratar(socio_id, datos.tipo, datos.referencia_pago, datos.fecha_inicio))


@router.get("/{socio_id}/membresia", response_model=MembresiaOut, summary="Consultar membresía con estado actualizado")
def obtener_membresia(socio_id: str, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.obtener(socio_id))


@router.post("/{socio_id}/membresia/renovacion", response_model=MembresiaOut, summary="Renovar membresía")
def renovar(socio_id: str, datos: PlanIn, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.renovar(socio_id, datos.tipo, datos.referencia_pago))


@router.post("/{socio_id}/membresia/mejora", response_model=MembresiaOut,
             summary="US-11 E2: mejorar plan (vencimiento desde el fin del mes actual)")
def mejorar(socio_id: str, datos: PlanIn, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.mejorar_plan(socio_id, datos.tipo, datos.referencia_pago))


@router.post("/{socio_id}/suspension", response_model=MembresiaOut, summary="US-06: suspender membresía")
def suspender(socio_id: str, datos: SuspensionIn, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.suspender(socio_id, datos.motivo))


@router.delete("/{socio_id}/suspension", response_model=MembresiaOut,
               summary="US-06 E2: regularizar (reactiva la membresía)")
def reactivar(socio_id: str, c: Container = Depends(get_container)):
    return membresia_out(c.membresias.reactivar(socio_id))


@router.get("/{socio_id}/notificaciones", summary="Notificaciones enviadas al socio")
def notificaciones(socio_id: str, c: Container = Depends(get_container)):
    c.socios.obtener(socio_id)
    return c.consultas.notificaciones(socio_id)


@router.get("/{socio_id}/accesos", summary="Historial de accesos del socio")
def accesos(socio_id: str, c: Container = Depends(get_container)):
    c.socios.obtener(socio_id)
    return c.consultas.accesos(socio_id)


@router.post("/{socio_id}/entrenamiento-personal", status_code=201,
             summary="US-13: contratar paquete de entrenamiento personal (requiere membresía vigente)")
def contratar_entrenamiento(socio_id: str, d: EntrenamientoIn, c: Container = Depends(get_container)):
    p = c.entrenamiento.contratar(socio_id, d.instructor_id, d.sesiones, d.referencia_pago)
    return {"id": p.id, "socio_id": p.socio_id, "instructor_id": p.instructor_id, "sesiones": p.sesiones,
            "incluido_en_plan": p.incluido_en_plan, "modulo_agenda_habilitado": p.modulo_agenda_habilitado}
