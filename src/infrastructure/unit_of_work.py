from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from ..application.ports import UnitOfWork
from .repositories import (
    SqlAccesoRepository, SqlClaseRepository, SqlEntrenamientoRepository, SqlInstructorRepository, SqlMembresiaRepository,
    SqlNotificacionRepository, SqlPagoRepository, SqlSocioRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Una sesión = una transacción. Si hay excepción, se hace rollback automático."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.socios = SqlSocioRepository(self.session)
        self.membresias = SqlMembresiaRepository(self.session)
        self.instructores = SqlInstructorRepository(self.session)
        self.clases = SqlClaseRepository(self.session)
        self.pagos = SqlPagoRepository(self.session)
        self.entrenamientos = SqlEntrenamientoRepository(self.session)
        self.accesos = SqlAccesoRepository(self.session)
        self.notificaciones = SqlNotificacionRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
        return False

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
