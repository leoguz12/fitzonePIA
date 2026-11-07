from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..container import Container
from ..deps import get_container
from ..schemas import AccesoIn, AccesoOut, acceso_out

router = APIRouter(prefix="/accesos", tags=["Control de acceso"])


@router.post("", response_model=AccesoOut, responses={403: {"model": AccesoOut, "description": "Alerta roja: acceso denegado"}},
             summary="US-01 / US-06 / US-14: validar ingreso en recepción o torniquete")
def validar_ingreso(datos: AccesoIn, c: Container = Depends(get_container)):
    resultado = c.accesos.validar_ingreso(datos.socio_id)
    if not resultado.permitido:
        return JSONResponse(status_code=403, content=acceso_out(resultado).model_dump())
    reservas = c.consultas.reservas_del_dia(datos.socio_id, c.deps.reloj().date())
    return acceso_out(resultado, jsonable(reservas))


def jsonable(filas: list[dict]) -> list[dict]:
    return [{**f, "inicio": f["inicio"].isoformat()} for f in filas]
