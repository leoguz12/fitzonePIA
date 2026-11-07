# Arquitectura de FitZone

Documento de decisiones técnicas. Los diagramas describen el **código final**; las decisiones están justificadas en los
[ADR](adr/README.md). Los diagramas de estados se generan desde el código ([state-machines.md](state-machines.md)).

## 1. Vista de capas (regla de dependencias)

```mermaid
flowchart LR
    subgraph API["api — controllers REST (FastAPI)"]
        R["routers · schemas · errores HTTP"]
    end
    subgraph APP["application — casos de uso"]
        S["Servicios de aplicación (orquestan)"]
        Q["Consultas CQRS (lectura)"]
        B["Event Bus + handlers"]
    end
    subgraph DOM["domain — negocio puro"]
        A["Aggregates · Entities · Value Objects"]
        SP["Specifications"]
        FSM["State Machines"]
        EV["Domain Events"]
        P["Puertos: repositorios (ABC)"]
    end
    subgraph INF["infrastructure — detalles técnicos"]
        REPO["Repositorios SQLAlchemy + Unit of Work"]
        RM["Read model SQL (SQLAlchemy Core)"]
        PG["Pasarela de pago (simulada)"]
    end
    R --> S
    R --> Q
    S --> A
    S --> B
    A --> SP
    A --> FSM
    A --> EV
    REPO -. "implementa" .-> P
    RM -. "implementa ReadModel" .-> Q
    PG -. "implementa PaymentGateway" .-> S
```

La regla `api → application → domain ← infrastructure` se **verifica automáticamente** en
[`tests/unit/test_arquitectura.py`](../../tests/unit/test_arquitectura.py): si el dominio importa SQLAlchemy, FastAPI o
cualquier capa externa, la prueba falla (y por tanto el pipeline de CI).

| Capa | Carpeta | Responsabilidad | Prohibido |
|---|---|---|---|
| Dominio | `src/domain/` | Reglas de negocio, invariantes, eventos | Conocer BD, HTTP o frameworks |
| Aplicación | `src/application/` | Casos de uso: cargar → ordenar al dominio → guardar → publicar eventos | Contener `if cupos > 0` (esa regla vive en el dominio) |
| Infraestructura | `src/infrastructure/` | SQLAlchemy, UoW, read model, pasarela de pago, configuración | Contener reglas de negocio |
| API | `src/api/` | Endpoints REST, esquemas, traducción error → HTTP, *composition root* | Acceder a la BD directamente |

## 2. Modelo de dominio (DDD)

```mermaid
classDiagram
    class Socio {
        <<Aggregate Root>>
        +str id
        +str nombre
        +str email
        +int advertencias
        +int no_shows
        +registrar_advertencia()
        +registrar_no_show()
    }
    class Membresia {
        <<Aggregate Root>>
        +str id
        +str socio_id
        +EstadoMembresia estado
        +validar_acceso(ahora)
        +suspender(motivo)
        +reactivar()
        +renovar(tipo)
        +mejorar_plan(tipo)
    }
    class ClaseEspecial {
        <<Aggregate Root>>
        +str id
        +str nombre
        +datetime inicio
        +str servicio_requerido
        +Decimal precio_extra
        +EstadoClase estado
        +cupos_disponibles int
        +reservar(socio_id)
        +unirse_lista_espera(socio_id)
        +cancelar_reserva(reserva_id)
        +asignar_desde_lista_espera()
        +registrar_asistencia(socio_id)
        +procesar_no_shows()
        +cancelar_sesion(instructor_id, motivo)
        +asignar_suplente(instructor_id)
        +finalizar()
    }
    class Reserva {
        <<Entity>>
        +str id
        +str socio_id
        +EstadoReserva estado
        +str pago_id
        +bool cancelada_tarde
    }
    class ListaEspera {
        <<Entity>>
        +agregar(socio_id)
        +retirar(socio_id)
        +extraer_primero()
    }
    class Pago {
        <<Aggregate Root>>
        +Decimal monto
        +EstadoPago estado
        +reembolsar()
    }
    class PaqueteEntrenamiento {
        <<Aggregate Root>>
        +int sesiones
        +bool incluido_en_plan
    }
    class Instructor {
        <<Entity>>
        +str id
        +str nombre
    }
    class Vigencia {
        <<Value Object>>
        +date fecha_inicio
        +date fecha_vencimiento
    }
    class PlanContratado {
        <<Value Object>>
        +TipoPlan tipo
        +frozenset servicios_incluidos
    }
    class CapacidadMaxima {
        <<Value Object>>
        +int limite
    }
    Socio "1" --> "0..1" Membresia : posee
    Socio "1" --> "*" Reserva : realiza
    Membresia *-- Vigencia
    Membresia *-- PlanContratado
    ClaseEspecial *-- Reserva
    ClaseEspecial *-- ListaEspera
    ClaseEspecial *-- CapacidadMaxima
    Instructor "1" --> "*" ClaseEspecial : imparte
    Reserva "0..1" --> "1" Pago : pagada con
    Socio "1" --> "*" PaqueteEntrenamiento : contrata
```

**Aggregate Roots:** `Socio`, `Membresia`, `ClaseEspecial`, `Pago`, `PaqueteEntrenamiento`. Los agregados se referencian
entre sí **solo por id** (`socio_id`, `pago_id`), nunca por objeto. `Reserva` y `ListaEspera` son entidades **internas** de
`ClaseEspecial`: no existen sin ella y solo ella puede crearlas (el equipo corrigió a la IA en este punto: ver bitácora de la Fase 2).
**Value Objects:** `Vigencia`, `PlanContratado`, `CapacidadMaxima` (inmutables, validan su invariante al crearse).
**Domain Service:** `solicitar_lugar` (`domain/services.py`) coordina `Membresia` + `ClaseEspecial`.
**Eventos de dominio:** ver `src/domain/events.py` (18 eventos; los publica el `EventBus` tras confirmar la transacción).

### Invariantes protegidos por los agregados

| Agregado | Invariante | Dónde |
|---|---|---|
| `ClaseEspecial` | Cupos disponibles ≥ 0 (nunca se excede la capacidad) | `reservar` → `CAPACIDAD_EXCEDIDA` |
| `ClaseEspecial` | Un socio no reserva dos veces la misma clase | `tiene_lugar` → `RESERVA_DUPLICADA` |
| `ClaseEspecial` | Una clase cancelada no admite reservas | estado + `CLASE_FSM` |
| `ListaEspera` | Orden estrictamente FIFO, sin duplicados | `agregar`, `extraer_primero` |
| `Membresia` | `fecha_vencimiento > fecha_inicio` | `Vigencia.__post_init__` |
| `Socio` | Datos de contacto válidos | `Socio.__init__` |
| `Pago` | Monto > 0; solo un pago aprobado puede reembolsarse | `Pago`, `PAGO_FSM` |

## 3. Persistencia (modelo físico)

```mermaid
erDiagram
    SOCIOS ||--o| MEMBRESIAS : posee
    SOCIOS ||--o{ RESERVAS : realiza
    SOCIOS ||--o{ PAGOS : paga
    SOCIOS ||--o{ PAQUETES_ENTRENAMIENTO : contrata
    INSTRUCTORES ||--o{ CLASES : imparte
    INSTRUCTORES ||--o{ PAQUETES_ENTRENAMIENTO : atiende
    CLASES ||--o{ RESERVAS : contiene
    CLASES ||--o{ LISTA_ESPERA : tiene
    SOCIOS ||--o{ ACCESOS : "historial (sin FK)"
    SOCIOS ||--o{ NOTIFICACIONES : "recibe (sin FK)"
```

Modelos ORM en `src/infrastructure/orm.py` (SQLAlchemy 2.0). Los repositorios traducen entre filas y objetos de dominio; el dominio nunca ve el ORM.

## 4. Flujos principales (secuencias del código final)

### 4.1 Reservar una clase (CU-02 / CU-03) — `POST /clases/{id}/reservas`

```mermaid
sequenceDiagram
    actor Socio
    participant API as API (router)
    participant RS as ReservaAppService
    participant DS as solicitar_lugar (Domain Service)
    participant CE as ClaseEspecial
    participant Bus as EventBus
    Socio->>API: POST /clases/{id}/reservas
    API->>RS: reservar(clase_id, socio_id)
    RS->>RS: cargar clase (bloqueo de fila) y membresía
    RS->>DS: solicitar_lugar(clase, membresía)
    alt Membresía vencida o suspendida
        DS-->>API: AccesoDenegadoError
        API-->>Socio: 403 (alerta, reserva denegada)
    else El plan NO incluye la clase
        DS-->>API: PlanNoIncluyeClaseError
        API-->>Socio: 402 requiere pago adicional (monto)
    else Hay cupo
        DS->>CE: reservar(socio_id)
        CE-->>RS: Reserva + ReservaConfirmada
        RS->>RS: commit (Unit of Work)
        RS->>Bus: publicar eventos
        API-->>Socio: 201 CONFIRMADA
    else Clase llena
        DS->>CE: unirse_lista_espera(socio_id)
        CE-->>RS: posición + CapacidadAlcanzada
        RS->>RS: commit
        RS->>Bus: publicar eventos
        API-->>Socio: 202 LISTA_ESPERA (posición)
    end
```

### 4.2 Cobro fuera de plan con compensación (CU-04) — `POST /clases/{id}/pagos-fuera-de-plan`

```mermaid
sequenceDiagram
    actor Recepcion as Recepción
    participant API
    participant RS as ReservaAppService
    participant PG as Pasarela de pago
    participant DB as Unit of Work
    Recepcion->>API: cobrar clase fuera de plan
    API->>RS: reservar_con_pago
    RS->>RS: validar elegibilidad, plan NO incluye, hay cupo
    RS->>PG: cobrar(monto)
    alt Pago rechazado
        PG-->>RS: rechazado
        RS->>DB: guardar Pago RECHAZADO + commit
        API-->>Recepcion: 402 PAGO_RECHAZADO (sin reserva)
    else Pago aprobado
        PG-->>RS: referencia
        RS->>DB: Pago APROBADO + Reserva (misma transacción)
        alt commit correcto
            API-->>Recepcion: 201 lugar habilitado
        else falla la operación después del cobro
            RS->>DB: rollback
            RS->>PG: reembolsar(referencia)
            RS->>DB: guardar Pago REEMBOLSADO
            API-->>Recepcion: error (no queda cobro sin reserva)
        end
    end
```

### 4.3 Asistencia, No-Show y asignación automática (US-05, US-07)

```mermaid
sequenceDiagram
    actor Recepcion as Recepción / Torniquete
    participant API
    participant AS as AsistenciaAppService
    participant CE as ClaseEspecial
    participant Bus as EventBus
    participant LE as ListaEsperaAppService
    actor Espera as Socio en lista de espera
    Recepcion->>API: POST /clases/{id}/asistencias
    API->>AS: registrar_asistencia
    AS->>CE: registrar_asistencia(socio, ahora, tolerancia)
    alt Llega DENTRO de la tolerancia
        CE-->>AS: ASISTIDA + AsistenciaRegistrada
        API-->>Recepcion: asistencia registrada
    else Llega FUERA de la tolerancia
        CE-->>AS: NO_SHOW + NoShowRegistrado + LugarLiberado
        AS->>Bus: publicar eventos (tras commit)
        Bus->>Bus: NoShowRegistrado → suma no-show al perfil y notifica
        Bus->>LE: LugarLiberado → asignar_vacante
        LE->>CE: asignar_desde_lista_espera (FIFO)
        CE-->>LE: Reserva + SocioAsignadoDesdeEspera
        Bus-->>Espera: notificación "¡Lugar asignado!"
        API-->>Recepcion: NO_SHOW, lugar reasignado
    end
```

## 5. Patrones aplicados y justificación

| Patrón | Dónde | Por qué (relación con el negocio) |
|---|---|---|
| **Domain Model** | `src/domain/` | Las reglas de aforo, vigencia y lista de espera son muchas y están acopladas; encapsularlas evita duplicar validaciones (ADR 0001) |
| **Service Layer** | `src/application/*_service.py` | Una sola entrada por caso de uso que orquesta sin contener reglas |
| **Repository** | `domain/repositories.py` + `infrastructure/repositories.py` | El dominio no conoce la BD (ADR 0001, 0004) |
| **Unit of Work** | `infrastructure/unit_of_work.py` | Reserva + cobro + lista de espera deben guardarse juntas o ninguna (ADR 0002) |
| **CQRS** | `application/queries.py` + `infrastructure/read_model.py` | Los reportes de demanda no deben cargar agregados completos ni frenar el torniquete (ADR 0003) |
| **Specification** | `domain/specifications.py` | Reglas de acceso/reserva/cancelación como objetos componibles (`&`, `\|`, `~`) que explican por qué fallaron (ADR 0005) |
| **State Machine** | `domain/state_machine.py` | Membresía, reserva, clase y pago tienen ciclos de vida con transiciones válidas explícitas (ADR 0006) |
| **Domain Events + Event Bus** | `domain/events.py`, `application/event_bus.py`, `handlers.py` | "Se liberó un lugar" dispara la lista de espera sin acoplar los agregados (ADR 0007) |
| **Domain Service** | `domain/services.py` | La decisión de reservar involucra dos agregados |
| **Adapter / Gateway** | `PaymentGateway` → `PasarelaSimulada` | Se cambia por una pasarela real sin tocar el negocio (ADR 0008) |
| **Dependency Injection / Composition Root** | `api/container.py` | Único lugar donde se conectan implementaciones concretas |

Los principios SOLID, con evidencia en el código, están en [solid.md](solid.md).

## 6. Evolución respecto al diseño de la Fase 2

El diseño de la Fase 2 (`docs/entregas_previas/U3_Reporte_Fase2_Diseno_Arquitectural.pdf`) se mantuvo en lo esencial
(Domain Model, DDD, Service Layer, Repository, UoW, CQRS, ADR 0001–0003). Estos son los ajustes que se hicieron al
implementarlo y por qué; **el UML y las secuencias de la Fase 2 quedaron como versión inicial** (se conservan en
`diagramas_fase2/`) y los vigentes son los de este documento:

| Tema | En la Fase 2 | En la implementación | Motivo |
|---|---|---|---|
| Lenguaje | Interfaces estilo C# (`Task<...>Async`) y Dapper | Python 3.12: clases abstractas (`ABC`) y SQLAlchemy Core para lecturas | El curso y los laboratorios U4/U5 usan Python + FastAPI (ADR 0004) |
| Comandos CQRS | Clases `...Command` y `...CommandHandler` | Métodos de los servicios de aplicación | Simplificación; la separación escritura (dominio) / lectura (read model) se conserva |
| `ReporteMensualQuery(mes, año)` | Reporte por mes | `reporte_demanda(desde, hasta)` | US-10 E2 exige filtro por rango de fechas |
| `PagoAppService` | Servicio aparte | Función `ejecutar_con_cobro` reutilizada por 3 servicios | Evita triplicar la lógica de compensación |
| `Socio.estatus` | Atributo del socio (UML) | El estatus vive en `Membresia.estado` | Un único dueño del estado de acceso (US-06) |
| `Instructor.cancelarSesion()` | Método del instructor | `ClaseEspecial.cancelar_sesion(instructor_id, ...)` | Solo el agregado `ClaseEspecial` puede cambiar su estado; el instructor se verifica con una Specification (titular **o** suplente) |
| `Reserva` | Entidad interna de `ClaseEspecial` | Igual | Se mantuvo la corrección de la bitácora de IA |
| `NoShowRegistrado` | "Lo detona el sistema de recepción" | Lo emite `ClaseEspecial` (`procesar_no_shows` / `registrar_asistencia`) | El agregado es dueño de sus reservas |
| Plan con "Membresía Diamante" por polimorfismo (OCP) | `PlanContratado` polimórfico | Catálogo de datos `SERVICIOS_POR_PLAN` | Más simple; agregar un plan es agregar datos, no tocar servicios |
| Entrenamiento personal | Solo en el glosario | `PaqueteEntrenamiento` (US-13) | Estaba en el alcance del BRD y no tenía implementación |
| Modo offline (US-14 E2) | No tratado | Fuera de alcance (ADR 0009) | Requiere un cliente de torniquete con caché local |
