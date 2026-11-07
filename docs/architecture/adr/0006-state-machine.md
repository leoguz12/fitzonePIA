# ADR 0006: State Machine declarativa para los ciclos de vida

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
Membresía (activa/suspendida/vencida), reserva (confirmada/cancelada/asistida/no-show), clase y pago tienen transiciones válidas que antes estarían dispersas en `if estado == ...`.

## Alternativas consideradas
Condicionales por estado en cada método (descartado: fácil de olvidar un caso). Librería externa de FSM (descartada: una tabla de transiciones de ~30 líneas basta).

## Decisión
`StateMachine` genérica con una tabla `(estado, disparador) → estado`; transición inválida lanza `InvalidTransition` (HTTP 409). Los diagramas de `docs/architecture/state-machines.md` se **generan desde esas tablas**.

## Consecuencias
- **Positivas:** Imposible hacer una transición no declarada; diagramas siempre iguales al código.
- **Negativas / riesgos:** Las condiciones de negocio extra (ej. vigencia al reactivar) siguen en los métodos del agregado.

## Trazabilidad
US-04, US-06, US-07, US-09, US-11, US-12
