"""Pruebas de arquitectura: la regla de dependencias de las capas se verifica automáticamente.

    api  ->  application  ->  domain   <-  infrastructure (implementa los puertos)

El dominio no puede conocer a nadie; la aplicación solo conoce al dominio (Dependency Inversion Principle).
"""
import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2] / "src"

PROHIBIDO = {
    "domain": ["sqlalchemy", "fastapi", "pydantic", "starlette", "src.application", "src.infrastructure", "src.api",
               "..application", "..infrastructure", "..api"],
    "application": ["sqlalchemy", "fastapi", "pydantic", "starlette", "..infrastructure", "..api",
                    "src.infrastructure", "src.api"],
}


def _imports(archivo: Path) -> set[str]:
    encontrados = set()
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            encontrados.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            encontrados.add("." * nodo.level + (nodo.module or ""))
    return encontrados


@pytest.mark.parametrize("capa", ["domain", "application"])
def test_la_capa_no_depende_de_capas_externas(capa):
    archivos = list((RAIZ / capa).glob("*.py"))
    assert archivos
    for archivo in archivos:
        for imp in _imports(archivo):
            for prohibido in PROHIBIDO[capa]:
                assert not (imp == prohibido or imp.startswith(prohibido + ".")), (
                    f"{archivo.name} ({capa}) importa '{imp}', que viola la regla de dependencias")
