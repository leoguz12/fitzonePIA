"""Traduce excepciones de dominio a respuestas HTTP (el dominio no conoce HTTP)."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain import errors as e

_ESTADOS: list[tuple[type, int]] = [
    (e.NotFound, 404),
    (e.InvalidData, 422),
    (e.InvalidTransition, 409),
    (e.BusinessRuleViolation, 409),
    (e.Forbidden, 403),
    (e.AccesoDenegadoError, 403),
    (e.PlanNoIncluyeClaseError, 402),
    (e.PagoRechazadoError, 402),
]


def _cuerpo(exc: e.DomainError) -> dict:
    cuerpo = {"codigo": exc.codigo, "mensaje": exc.mensaje}
    if isinstance(exc, e.PlanNoIncluyeClaseError):
        cuerpo["monto_adicional"] = str(exc.monto)
    if isinstance(exc, e.AccesoDenegadoError):
        cuerpo["motivos"] = exc.codigos
    return cuerpo


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(e.DomainError)
    async def _dominio(request: Request, exc: e.DomainError) -> JSONResponse:
        estado = next((s for tipo, s in _ESTADOS if isinstance(exc, tipo)), 400)
        return JSONResponse(status_code=estado, content=_cuerpo(exc))
