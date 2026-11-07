# ADR 0007: Eventos de dominio en proceso (Event Bus)

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
"Se liberó un lugar" debe asignar al primero de la lista, notificar y sancionar, sin que `ClaseEspecial` conozca esas piezas.

## Alternativas consideradas
Llamadas directas entre servicios (descartado: acoplamiento). Cola de mensajes externa (descartada: excesiva para este alcance).

## Decisión
Los agregados acumulan eventos; el servicio de aplicación los publica en un `EventBus` **después del commit**. Los handlers (`handlers.py`) abren su propia transacción: asignar vacante, registrar no-show/advertencia, notificar, registrar acceso.

## Consecuencias
- **Positivas:** Desacoplamiento; agregar una reacción es suscribir un handler.
- **Negativas / riesgos:** Consistencia eventual dentro de la petición: si un handler falla, la operación principal ya está confirmada. Un *outbox* + cola sería el siguiente paso en producción.

## Trazabilidad
US-03, US-04, US-05, US-07, US-09
