"""Configuración desde variables de entorno (12-Factor App, factor III)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from ..application.reglas import ReglasNegocio
from ..domain.value_objects import TipoPlan


def _bool(valor: str | None, defecto: bool = False) -> bool:
    if valor is None:
        return defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí"}


def normalizar_url(url: str) -> str:
    """Render/Heroku entregan ``postgres://`` o ``postgresql://``; SQLAlchemy+psycopg3 necesita el driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./fitzone.db"
    app_env: str = "development"
    tolerancia_minutos: int = 10
    limite_cancelacion_horas: int = 2
    tarifa_mensual: Decimal = Decimal("600.00")
    tarifa_trimestral: Decimal = Decimal("1500.00")
    tarifa_anual: Decimal = Decimal("5000.00")
    tarifa_sesion_entrenamiento: Decimal = Decimal("300.00")
    seed_demo_data: bool = False

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = os.environ if env is None else env
        return cls(
            database_url=normalizar_url(e.get("DATABASE_URL", cls.database_url)),
            app_env=e.get("APP_ENV", cls.app_env),
            tolerancia_minutos=int(e.get("TOLERANCIA_MINUTOS", cls.tolerancia_minutos)),
            limite_cancelacion_horas=int(e.get("LIMITE_CANCELACION_HORAS", cls.limite_cancelacion_horas)),
            tarifa_mensual=Decimal(e.get("TARIFA_MENSUAL", str(cls.tarifa_mensual))),
            tarifa_trimestral=Decimal(e.get("TARIFA_TRIMESTRAL", str(cls.tarifa_trimestral))),
            tarifa_anual=Decimal(e.get("TARIFA_ANUAL", str(cls.tarifa_anual))),
            tarifa_sesion_entrenamiento=Decimal(e.get("TARIFA_SESION_ENTRENAMIENTO", str(cls.tarifa_sesion_entrenamiento))),
            seed_demo_data=_bool(e.get("SEED_DEMO_DATA")),
        )

    def reglas(self) -> ReglasNegocio:
        return ReglasNegocio(
            tolerancia=timedelta(minutes=self.tolerancia_minutos),
            limite_cancelacion=timedelta(hours=self.limite_cancelacion_horas),
            tarifa_sesion_entrenamiento=self.tarifa_sesion_entrenamiento,
            tarifas={
                TipoPlan.MENSUAL: self.tarifa_mensual,
                TipoPlan.TRIMESTRAL: self.tarifa_trimestral,
                TipoPlan.ANUAL: self.tarifa_anual,
            },
        )
