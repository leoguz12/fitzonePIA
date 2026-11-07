# ADR 0009: Modo offline del torniquete fuera del alcance de la API

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA (alcance) |

## Contexto
US-14 E2 pide que, sin internet, el sistema opere en modo local con los últimos datos sincronizados. Eso ocurre en el dispositivo del torniquete, no en el servidor.

## Alternativas consideradas
Implementarlo en la API (descartado: la API no puede responder si no hay red). Ignorarlo sin dejar constancia (descartado).

## Decisión
No se implementa en este proyecto. Se documenta como trabajo futuro: un cliente de torniquete con caché de vigencias y sincronización. US-14 E1 sí se implementa y se prueba (validación en < 2 s).

## Consecuencias
- **Positivas:** Alcance realista y honesto; el resto de US-14 queda cubierto.
- **Negativas / riesgos:** El escenario 2 de US-14 queda sin implementación ni prueba (la matriz de trazabilidad lo marca).

## Trazabilidad
US-14
