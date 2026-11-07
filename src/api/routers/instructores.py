from datetime import date

from fastapi import APIRouter, Depends

from ..container import Container
from ..deps import get_container
from ..schemas import InstructorIn

router = APIRouter(prefix="/instructores", tags=["Instructores"])


@router.post("", status_code=201, summary="Registrar instructor")
def registrar(datos: InstructorIn, c: Container = Depends(get_container)):
    i = c.clases.registrar_instructor(datos.nombre)
    return {"id": i.id, "nombre": i.nombre}


@router.get("/{instructor_id}/clases", summary="US-08: horario y aforo de las clases del instructor en una fecha")
def clases_del_dia(instructor_id: str, fecha: date, c: Container = Depends(get_container)):
    return c.consultas.clases_de_instructor(instructor_id, fecha)
