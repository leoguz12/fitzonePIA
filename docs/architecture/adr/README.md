# Registro de decisiones de arquitectura (ADR)

Formato: contexto, alternativas, decisión, consecuencias y trazabilidad a las historias de usuario.

| ADR | Decisión | Estado |
|---|---|---|
| [0001](0001-domain-model.md) | Implementación del patrón Domain Model | ACEPTADA (Fase 2, ratificada) |
| [0002](0002-unit-of-work.md) | Separación transaccional con Unit of Work | ACEPTADA (Fase 2, ratificada) |
| [0003](0003-cqrs.md) | CQRS para consultas masivas | ACEPTADA (Fase 2, actualizada) |
| [0004](0004-stack-tecnologico.md) | Stack tecnológico: Python, FastAPI, SQLAlchemy y PostgreSQL | ACEPTADA |
| [0005](0005-specification.md) | Patrón Specification para reglas de acceso y reserva | ACEPTADA |
| [0006](0006-state-machine.md) | State Machine declarativa para los ciclos de vida | ACEPTADA |
| [0007](0007-eventos-de-dominio.md) | Eventos de dominio en proceso (Event Bus) | ACEPTADA |
| [0008](0008-compensacion-de-pagos.md) | Cobros con compensación (reembolso) en lugar de confiar en el rollback | ACEPTADA |
| [0009](0009-modo-offline-fuera-de-alcance.md) | Modo offline del torniquete fuera del alcance de la API | ACEPTADA (alcance) |
| [0010](0010-contenedores-12-factor.md) | Contenedores y 12-Factor App | ACEPTADA |
| [0011](0011-sin-autenticacion.md) | Sin autenticación ni roles de usuario en esta versión | ACEPTADA (alcance) |
| [0012](0012-concurrencia.md) | Concurrencia: bloqueo de fila al modificar una clase | ACEPTADA |
