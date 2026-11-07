# ADR 0012: Concurrencia: bloqueo de fila al modificar una clase

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
Dos socios podrían reservar el **último cupo** al mismo tiempo y exceder la capacidad.

## Alternativas consideradas
Sin control (descartado: viola el invariante principal). Bloqueo optimista con versión (válido, pero requiere reintentos en el cliente).

## Decisión
Todos los casos de uso que modifican una clase la cargan con `with_for_update` (`ClaseRepository.get(..., bloquear=True)`): PostgreSQL serializa las escrituras sobre esa fila. El invariante `cupos ≥ 0` se vuelve a comprobar dentro del agregado.

## Consecuencias
- **Positivas:** No se sobre-reserva el último lugar.
- **Negativas / riesgos:** SQLite ignora `FOR UPDATE`; el comportamiento concurrente real solo se da en PostgreSQL (la lógica del invariante sí está probada con ambas).

## Trazabilidad
US-02, US-15
