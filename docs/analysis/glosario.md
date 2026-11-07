# Glosario de dominio — lenguaje ubicuo de FitZone

Fuente: Unidad 2 (`docs/entregas_previas/U2_Glosario_FitZone.pdf`, 20 términos). La columna **En el código** enlaza cada
término con la clase o función que lo implementa: el vocabulario del negocio es el mismo que usa el software.

| # | Concepto | Definición (lenguaje ubicuo) | En el código |
|---|---|---|---|
| 1 | **Socio** | Cliente registrado en FitZone que posee una membresía válida para ingresar a las instalaciones. | `domain/socio.py::Socio` (Aggregate Root) |
| 2 | **Membresía** | Servicio contratado (mensual, trimestral o anual) que dicta el nivel de acceso y los servicios incluidos. | `domain/membresia.py::Membresia` (Aggregate Root) |
| 3 | **Plan Contratado** | Nivel de suscripción que determina a qué servicios, áreas y clases especiales tiene acceso el socio. | `value_objects.py::PlanContratado` (Value Object) |
| 4 | **Recepción** | Área y rol que identifica a los socios y valida su acceso según las restricciones de su membresía. | `application/acceso_service.py::AccesoAppService`, `POST /accesos` |
| 5 | **Instructor** | Rol que imparte las clases especiales, responsable de la sesión y con autoridad para cancelarla. | `domain/instructor.py::Instructor` (Entity), `puede_gestionar_sesion()` |
| 6 | **Administrador** | Rol con privilegios operativos superiores: supervisa, gestiona reportes y administra membresías. | `GET /reportes/demanda`, `PUT /clases/{id}/instructor-suplente` |
| 7 | **Clase Especial** | Sesión de ejercicio con horario, instructor asignado y capacidad máxima estricta de asistentes. | `domain/clase_especial.py::ClaseEspecial` (Aggregate Root) |
| 8 | **Entrenamiento Personal** | Servicio adicional que puede o no estar incluido según el plan, sujeto a disponibilidad. | `domain/entrenamiento.py::PaqueteEntrenamiento` |
| 9 | **Reserva** | Acción mediante la cual un socio aparta su lugar en una clase especial antes de que el cupo se agote. | `clase_especial.py::Reserva` (Entity interna), `ClaseEspecial.reservar` |
| 10 | **Capacidad Máxima** | Restricción física y del sistema que limita los cupos de una clase. | `value_objects.py::CapacidadMaxima` (Value Object) |
| 11 | **Lista de Espera** | Registro secuencial de socios interesados en una clase que ya alcanzó su capacidad máxima. | `clase_especial.py::ListaEspera` (Entity, FIFO) |
| 12 | **No-show** | Infracción operativa: el socio reserva pero no asiste, dejando un lugar vacío sin aprovechar. | `EstadoReserva.NO_SHOW`, evento `NoShowRegistrado` |
| 13 | **Liberación de Espacio** | Mecanismo que, al cancelarse una reserva, otorga el lugar al siguiente socio en la lista de espera. | evento `LugarLiberado` → `ListaEsperaAppService.asignar_vacante` |
| 14 | **Fecha de Inicio** | Día a partir del cual los permisos de ingreso de una membresía se activan. | `Vigencia.fecha_inicio` |
| 15 | **Fecha de Vencimiento** | Límite temporal tras el cual se bloquea automáticamente el acceso del socio. | `Vigencia.fecha_vencimiento`, `MembresiaVigente` |
| 16 | **Membresía Vencida o Suspendida** | Estado irregular de una cuenta que desencadena la restricción de acceso en recepción. | `EstadoMembresia.VENCIDA / SUSPENDIDA` |
| 17 | **Cancelación de Reserva** | Acción del socio para renunciar a su cupo; debe ocurrir con anticipación para activar la liberación sin advertencia. | `ClaseEspecial.cancelar_reserva`, `CancelacionATiempo` |
| 18 | **Cancelación de Clase** | Excepción donde una sesión programada no se lleva a cabo (ej. ausencia del instructor). | `ClaseEspecial.cancelar_sesion`, evento `ClaseCancelada` |
| 19 | **Validación de Acceso** | Proceso en recepción para comprobar que el socio está activo y su plan incluye lo que intenta usar. | `Membresia.validar_acceso`, `acceso_permitido()` |
| 20 | **Demanda de Clases** | Métrica de reservas y listas de espera por sesión, clave para decisiones de horarios. | `SqlReadModel.reporte_demanda` |

## Términos incorporados al implementar

| Concepto | Definición | En el código |
|---|---|---|
| **Cancelación tardía** | Cancelación hecha dentro de las últimas 2 h antes de la clase: libera el lugar pero deja una advertencia. | `CancelacionTardiaRegistrada`, `Socio.advertencias` |
| **Tolerancia** | Minutos después del inicio de la clase durante los que aún se acepta la llegada del socio. | `DentroDeTolerancia`, `TOLERANCIA_MINUTOS` |
| **Pago fuera de plan** | Cobro en mostrador para tomar una clase que el plan no incluye. | `Pago`, `ejecutar_con_cobro` |
| **Instructor suplente** | Instructor que reemplaza al titular sin cancelar la clase. | `ClaseEspecial.instructor_suplente_id` |
| **Aforo** | Capacidad, inscritos y lugares disponibles de una clase en un momento dado. | `GET /clases/{id}/aforo` |
