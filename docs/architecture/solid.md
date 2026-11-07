# Aplicación de los principios SOLID (con evidencia en el código)

Cada principio indica **dónde se aplica** y **cómo comprobarlo**. Donde un hallazgo obligó a rediseñar, se documenta.

## S — Single Responsibility (una sola razón para cambiar)

| Clase / módulo | Única responsabilidad | Qué quedó fuera (y dónde vive) |
|---|---|---|
| `ReservaAppService` | Orquestar: cargar → pedir al dominio → guardar → publicar eventos | La regla de cupo vive en `ClaseEspecial`; la de vigencia, en `Membresia` / Specifications |
| `ejecutar_con_cobro` (`application/pagos.py`) | Cobrar y compensar (reembolsar) si la operación posterior falla | **Hallazgo y refactor:** esta lógica estaba pensada dentro de cada servicio; se extrajo porque Membresía, Reserva y Entrenamiento la necesitaban y el cobro es una responsabilidad distinta a reservar o contratar |
| `ReglasNegocio` | Parámetros configurables (tolerancia, tarifas) | Las reglas que los usan están en el dominio |
| `Vigencia` | Calcular y validar el rango de fechas | `Membresia` solo decide qué hacer con él |
| `handlers.py` | Reaccionar a eventos (notificar, sancionar, registrar acceso) | Quien emite el evento no sabe quién escucha |

**Verificación:** los servicios de `src/application/` no contienen comparaciones de reglas de negocio (`cupos`, `vigencia`...);
`grep -rn --include=*.py cupos_disponibles src/application src/api` no devuelve ninguna coincidencia: el atributo que expresa la regla de aforo solo se usa en el dominio. Fuera de él, la palabra "cupos" aparece únicamente en textos de documentación y en la consulta de solo lectura (`read_model.py`), que *muestra* el dato sin decidir nada.

## O — Open/Closed (abierto a extensión, cerrado a modificación)

- **Nuevos planes:** `SERVICIOS_POR_PLAN` es un catálogo de datos. Agregar un plan es agregar una entrada (más su tarifa); `ReservaAppService`, `Membresia` y `PlanIncluyeServicio` no cambian.
- **Nuevas reglas de acceso o reserva:** se escribe otra `Specification` y se compone con `&`, `|` o `~` en `puede_reservar()` / `acceso_permitido()`; ningún servicio cambia. `puede_gestionar_sesion()` ya usa `|` (titular **o** suplente).
- **Nuevas reacciones a eventos:** `bus.suscribir(Evento, handler)`; el agregado que emite el evento no se modifica (ej. enviar correo al confirmar una reserva es un handler más).
- *Límite honesto:* agregar un plan sí obliga a tocar el enum `TipoPlan` (sus propiedades `meses` y `nivel`) y la configuración de tarifas; son datos, no lógica de servicios.

## L — Liskov Substitution (los sustitutos cumplen el contrato)

- Cualquier `SocioRepository`, `ClaseRepository`... implementa su clase abstracta (`domain/repositories.py`) y devuelve objetos de dominio con el mismo comportamiento.
  **Evidencia:** la suite está preparada para correr contra SQLite (por defecto) o contra PostgreSQL (`docker compose --profile test run --rm tests`, variable `TEST_DATABASE_URL`) sin cambiar el dominio.
- `PasarelaSimulada` sustituye a cualquier `PaymentGateway` (cobrar/reembolsar); el servicio no distingue una real de la simulada.
- `AndSpecification`, `OrSpecification` y `NotSpecification` son `Specification`: se pueden anidar en cualquier lugar donde se espere una regla (`test_specification_and_or_not_componen`).

## I — Interface Segregation (interfaces pequeñas y específicas)

- No existe un `IRepository` gigante: hay un puerto por agregado, con solo los métodos que se usan (`InstructorRepository`: `add`, `get`; `PagoRepository`: `add`, `get`).
- El **lado de lectura** (`ReadModel`) está separado de los repositorios de escritura: los reportes no dependen de los métodos de guardado y viceversa (CQRS, ADR 0003).
- `AccesoRepository` y `NotificacionRepository` solo exponen `add`: los handlers que registran accesos no pueden modificar reservas.

## D — Dependency Inversion (depender de abstracciones)

- `src/domain/` y `src/application/` **no importan** SQLAlchemy, FastAPI, ni la infraestructura. Se verifica automáticamente en [`tests/unit/test_arquitectura.py`](../../tests/unit/test_arquitectura.py) (probado también con una violación intencional: la prueba falla).
- Los servicios reciben sus colaboradores por constructor mediante `Dependencias` (UoW, reloj, pasarela, bus, reglas, read model).
- El único lugar que conoce las implementaciones concretas es el *composition root*: [`src/api/container.py`](../../src/api/container.py).
- El **reloj** también se inyecta (`Clock`): las pruebas de tolerancia, cancelación tardía y vencimientos controlan el tiempo sin esperar ni parchear `datetime`.
