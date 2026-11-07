# ADR 0005: Patrón Specification para reglas de acceso y reserva

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
Las reglas "membresía vigente", "no suspendida", "plan incluye la clase", "cancelación a tiempo", "dentro de tolerancia" se combinan de distintas formas según el caso y recepción necesita saber **por qué** se negó algo.

## Alternativas consideradas
`if/else` anidados en los servicios (descartado: se duplican y no explican el motivo). Reglas como métodos sueltos del agregado (descartado: no se pueden combinar ni probar por separado).

## Decisión
Cada regla es una clase `Specification` con `is_satisfied_by` y `explicar`; se componen con `&`, `|`, `~`. Políticas: `acceso_permitido()`, `puede_reservar()`, `puede_gestionar_sesion()` (titular **o** suplente).

## Consecuencias
- **Positivas:** Reglas pequeñas, reutilizables y probadas una a una; el motivo del rechazo (alerta roja, US-06) sale de la propia regla.
- **Negativas / riesgos:** Más clases; hay que cuidar la convención de mensajes de las reglas negadas.

## Trazabilidad
US-01, US-02, US-04, US-06, US-07, US-09, US-14
