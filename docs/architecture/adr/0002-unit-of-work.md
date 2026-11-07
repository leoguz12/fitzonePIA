# ADR 0002: Separación transaccional con Unit of Work

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA (Fase 2, ratificada) |

## Contexto
Procesos como reservar + cobrar, o liberar un lugar + asignarlo, modifican varias entidades a la vez.

## Alternativas consideradas
Guardar cada repositorio por separado (descartado: puede dejar datos a medias).

## Decisión
`SqlAlchemyUnitOfWork`: una sesión por caso de uso con `commit` explícito y `rollback` automático si hay excepción. Los eventos se publican **después** del commit.

## Consecuencias
- **Positivas:** No se corrompen datos ante fallos a mitad del proceso. Probado en `test_unit_of_work_rollback_*`.
- **Negativas / riesgos:** Un rollback de base de datos no deshace un cobro externo: eso se resuelve con el ADR 0008.

## Trazabilidad
US-02, US-04, US-05, US-11, US-12, US-13
