# ADR 0004: Stack tecnológico: Python, FastAPI, SQLAlchemy y PostgreSQL

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
La Fase 2 esbozó interfaces con sintaxis C#/.NET y Dapper, pero los laboratorios U4 y U5 del curso se hicieron en Python + FastAPI + pytest + SQLAlchemy, y el PIA exige API REST documentada, pruebas y CI/CD.

## Alternativas consideradas
C#/.NET (descartado: no es lo practicado en U4/U5). Django (descartado: su ORM y su estructura empujan a un modelo anémico). Solo SQLite (descartado: producción necesita un motor cliente-servidor).

## Decisión
Python 3.12 + **FastAPI** (OpenAPI/Swagger automático) + **SQLAlchemy 2** (ORM para escritura, Core para lectura) + **PostgreSQL 16** en Docker/producción; SQLite en memoria para pruebas rápidas.

## Consecuencias
- **Positivas:** Swagger UI sin esfuerzo extra; pruebas rápidas; mismo código sobre SQLite y PostgreSQL.
- **Negativas / riesgos:** Python no impone tipos en tiempo de compilación (se mitiga con anotaciones y pruebas).

## Trazabilidad
Todo el sistema (reemplaza supuestos de lenguaje de la Fase 2)
