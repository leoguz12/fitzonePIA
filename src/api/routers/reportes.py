from datetime import date

from fastapi import APIRouter, Depends

from ..container import Container
from ..deps import get_container

router = APIRouter(prefix="/reportes", tags=["Reportes (CQRS - lectura)"])


@router.get("/demanda", summary="US-10: tasa de ocupación y lugares vacíos por clase, con filtro de fechas")
def demanda(desde: date, hasta: date, c: Container = Depends(get_container)):
    return c.consultas.reporte_demanda(desde, hasta)
