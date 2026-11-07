# syntax=docker/dockerfile:1
# Etapas: base -> test -> runtime. La ÚLTIMA etapa (runtime) es la que se despliega por defecto.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

# --- Pruebas: docker compose --profile test run --rm tests ---
FROM base AS test
RUN pip install -r requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
CMD ["pytest", "--cov=src", "--cov-report=term-missing", "--cov-fail-under=80"]

# --- Producción ---
FROM base AS runtime
RUN pip install -r requirements.txt
COPY src ./src
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
# PORT lo inyectan plataformas como Render/Railway; en local usa 8000
CMD ["sh", "-c", "uvicorn src.api.asgi:app --host 0.0.0.0 --port ${PORT:-8000}"]
