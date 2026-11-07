# ADR 0001: Implementación del patrón Domain Model

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA (Fase 2, ratificada) |

## Contexto
FitZone tiene reglas de aforo, vigencia y plan fuertemente acopladas entre sí. Con Transaction Script habría que repetir las validaciones en cada caso de uso.

## Alternativas consideradas
Transaction Script (descartado: duplica validaciones, nula protección de invariantes). Table Module (descartado: se acopla al modelo entidad-relación y coordina mal reglas entre tablas).

## Decisión
Adoptar **Domain Model**: agregados `Socio`, `Membresia`, `ClaseEspecial`, `Pago`, `PaqueteEntrenamiento` con sus invariantes; el dominio no conoce la base de datos (puertos en `domain/repositories.py`).

## Consecuencias
- **Positivas:** Alta cohesión; el código usa el lenguaje ubicuo del glosario; los invariantes (cupos ≥ 0) no se pueden saltar.
- **Negativas / riesgos:** Curva de aprendizaje de DDD para todo el equipo; más clases que un CRUD.

## Trazabilidad
US-01, US-02, US-03, US-06, US-07, US-13, US-15
