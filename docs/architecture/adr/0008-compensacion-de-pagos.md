# ADR 0008: Cobros con compensación (reembolso) en lugar de confiar en el rollback

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
El reporte U5 identificó el defecto de mayor impacto: **cobrar una clase fuera de plan sin registrar la reserva**. Un rollback de SQLAlchemy no cancela un cobro bancario.

## Alternativas consideradas
Reservar primero y cobrar después (descartado: se asignaría un lugar sin pagar). Confiar en el rollback (descartado: no revierte el banco).

## Decisión
`ejecutar_con_cobro`: cobra; si se rechaza, guarda el `Pago` RECHAZADO y falla; si se aprueba, ejecuta la operación en la misma transacción y, **si algo falla, hace rollback, reembolsa por la pasarela y guarda el `Pago` como REEMBOLSADO**. Solo se cobra si hay cupo disponible.

## Consecuencias
- **Positivas:** No queda dinero cobrado sin reserva; hay constancia de cada intento. Probado con un fallo inyectado después del cobro.
- **Negativas / riesgos:** Con una pasarela real habría que añadir idempotencia y reintentos del reembolso (la pasarela es simulada).

## Trazabilidad
US-12, US-11, US-13
