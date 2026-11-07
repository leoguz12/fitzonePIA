"""Exporta la especificación OpenAPI a docs/api/openapi.json.

Uso:  python scripts/export_openapi.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.api.main import create_app  # noqa: E402
from src.infrastructure.config import Settings  # noqa: E402

app = create_app(Settings(database_url="sqlite://"))
destino = RAIZ / "docs" / "api" / "openapi.json"
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"OpenAPI exportado en {destino.relative_to(RAIZ)}")
