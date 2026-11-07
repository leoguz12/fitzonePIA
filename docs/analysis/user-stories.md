# Historias de usuario y criterios de aceptación (Gherkin)

Fuente: entrega de la Unidad 2 (`docs/entregas_previas/U2_User_Stories_FitZone.pdf`). 15 historias, 30 escenarios. Cada escenario está en `docs/analysis/gherkin/US-XX.feature` y enlazado con su código y prueba en [`docs/traceability.md`](../traceability.md).

## [US-01] Identificación y Acceso en Recepción

- **Rol:** Socio
- **Historia:** Como socio, quiero identificarme en recepción, para poder ingresar a las instalaciones a entrenar.

**Criterios de aceptación**

**Escenario 1: Acceso exitoso**

- **Given:** el socio tiene una membresía vigente.
- **When:** presenta su identificación en recepción.
- **Then:** el sistema permite el acceso y registra la entrada.

**Escenario 2: Membresía vencida**

- **Given:** la membresía del socio ha superado su fecha de vencimiento.
- **When:** presenta su identificación.
- **Then:** el sistema arroja alerta roja y deniega el paso.

## [US-02] Reservación de Clase Específica

- **Rol:** Socio
- **Historia:** Como socio, quiero reservar un lugar en una clase específica, para asegurar mi participación antes de que se llene.

**Criterios de aceptación**

**Escenario 1: Reserva confirmada**

- **Given:** una clase tiene lugares disponibles bajo su capacidad máxima.
- **When:** el socio confirma la reservación.
- **Then:** el sistema le asigna el lugar y reduce en 1 el cupo disponible.

**Escenario 2: Restricción por plan**

- **Given:** la clase solicitada no está incluida en el plan del socio.
- **When:** intenta reservar la clase.
- **Then:** el sistema bloquea la reserva y notifica que requiere un pago adicional.

## [US-03] Ingreso a Lista de Espera

- **Rol:** Socio
- **Historia:** Como socio, quiero anotarme en una lista de espera, para tener oportunidad de entrar si alguien cancela.

**Criterios de aceptación**

**Escenario 1: Ingreso a lista**

- **Given:** la clase alcanzó su capacidad máxima.
- **When:** el socio solicita reservar el horario.
- **Then:** el sistema lo agrega al final de la lista de espera.

**Escenario 2: Abandono de lista**

- **Given:** el socio está en la lista de espera.
- **When:** decide que ya no quiere asistir y se retira.
- **Then:** el sistema lo remueve y recorre los lugares subsecuentes.

## [US-04] Cancelación de Reservación

- **Rol:** Socio
- **Historia:** Como socio, quiero cancelar mi reservación de clase, para liberar mi lugar si no podré asistir.

**Criterios de aceptación**

**Escenario 1: Cancelación a tiempo**

- **Given:** el socio tiene una reserva activa.
- **When:** cancela su asistencia antes del límite de tiempo.
- **Then:** el sistema libera el lugar para otro socio.

**Escenario 2: Cancelación tardía**

- **Given:** el socio cancela fuera del tiempo permitido.
- **When:** procesa la cancelación.
- **Then:** el sistema libera el lugar pero registra una advertencia en el perfil del socio.

## [US-05] Asignación Automática desde Lista de Espera

- **Rol:** Administrador
- **Historia:** Como administrador, quiero que la lista de espera asigne lugares automáticamente, para evitar la gestión manual y lugares ociosos.

**Criterios de aceptación**

**Escenario 1: Asignación automática**

- **Given:** existe una lista de espera y se libera un lugar.
- **When:** el sistema detecta la vacante.
- **Then:** asigna el espacio automáticamente al primer socio de la lista.

**Escenario 2: Lista de espera vacía**

- **Given:** se libera un lugar pero no hay nadie en lista de espera.
- **When:** el sistema procesa la cancelación.
- **Then:** el lugar vuelve a aparecer como disponible en el catálogo general.

## [US-06] Bloqueo por Cuentas Suspendidas

- **Rol:** Recepción
- **Historia:** Como recepción, quiero visualizar alertas de cuentas suspendidas, para aplicar las restricciones correspondientes.

**Criterios de aceptación**

**Escenario 1: Bloqueo por suspensión**

- **Given:** un socio tiene el estatus de membresía "suspendida".
- **When:** solicita acceso en recepción.
- **Then:** el sistema muestra el motivo y bloquea la operación.

**Escenario 2: Regularización**

- **Given:** el socio suspendido regulariza su situación.
- **When:** recepción actualiza el estatus a activo.
- **Then:** el sistema restaura los privilegios de reserva y acceso.

## [US-07] Registro Automático de No-Shows

- **Rol:** Administrador
- **Historia:** Como administrador, quiero registrar de forma automática los no-shows, para medir la inasistencia y aplicar políticas.

**Criterios de aceptación**

**Escenario 1: Etiquetado de No-Show**

- **Given:** la clase ha comenzado y un socio reservó pero no pasó asistencia.
- **When:** transcurre el tiempo de tolerancia.
- **Then:** el sistema etiqueta la reserva como no-show y guarda el registro.

**Escenario 2: Asistencia tardía**

- **Given:** el socio llega dentro de los minutos de tolerancia.
- **When:** registra su entrada en recepción.
- **Then:** el sistema valida su asistencia y no genera el reporte de no-show.

## [US-08] Consulta de Aforo por Instructor

- **Rol:** Instructor
- **Historia:** Como instructor, quiero consultar el horario y el aforo de mis clases, para preparar la sesión adecuadamente.

**Criterios de aceptación**

**Escenario 1: Consulta de aforo**

- **Given:** el instructor accede a su portal de gestión.
- **When:** selecciona la clase del día.
- **Then:** el sistema despliega la capacidad máxima y el número de reservas actuales.

**Escenario 2: Clase sin reservas**

- **Given:** la clase programada no tiene ningún socio inscrito.
- **When:** el instructor revisa el horario.
- **Then:** el sistema indica "0 inscritos" y permite gestionar la cancelación preventiva.

## [US-09] Cancelación de Sesión por Instructor

- **Rol:** Instructor
- **Historia:** Como instructor, quiero cancelar una sesión en el sistema, para notificar a los alumnos en caso de imprevistos.

**Criterios de aceptación**

**Escenario 1: Cancelación notificada**

- **Given:** una clase cuenta con reservaciones activas.
- **When:** el instructor cancela la sesión desde su panel.
- **Then:** el sistema envía notificaciones a los socios inscritos y libera sus cupos.

**Escenario 2: Instructor suplente**

- **Given:** el instructor titular no puede asistir pero hay un reemplazo.
- **When:** el administrador asigna al instructor suplente en el sistema.
- **Then:** la clase se mantiene activa y se notifica el cambio de instructor a los socios.

## [US-10] Reportes de Demanda de Clases

- **Rol:** Administrador
- **Historia:** Como administrador, quiero generar reportes de reservas y asistencias, para medir la demanda de las clases.

**Criterios de aceptación**

**Escenario 1: Generación de reporte**

- **Given:** existen registros históricos de clases impartidas.
- **When:** el administrador solicita el reporte de demanda.
- **Then:** el sistema despliega la tasa de ocupación y los lugares vacíos por clase.

**Escenario 2: Filtro por fechas**

- **Given:** el administrador requiere datos específicos.
- **When:** aplica un filtro de fechas para el último mes.
- **Then:** el sistema ajusta las métricas exclusivamente a ese periodo.

## [US-11] Adquisición de Plan Trimestral

- **Rol:** Socio
- **Historia:** Como socio, quiero comprar un plan trimestral, para asegurar mi acceso por ese periodo de tiempo.

**Criterios de aceptación**

**Escenario 1: Alta trimestral**

- **Given:** un usuario realiza el pago de la cuota trimestral.
- **When:** el sistema registra la transacción de inscripción.
- **Then:** se establece la fecha de vencimiento exactamente a tres meses de la fecha de inicio.

**Escenario 2: Upgrade de membresía**

- **Given:** el socio tiene un plan mensual activo y compra el anual.
- **When:** se procesa el pago del nuevo plan.
- **Then:** el sistema recalcula el vencimiento sumando el año a partir del fin del mes actual.

## [US-12] Cobro de Clases Fuera de Plan

- **Rol:** Recepción
- **Historia:** Como recepción, quiero procesar pagos de clases fuera de plan, para autorizar el acceso a servicios exclusivos.

**Criterios de aceptación**

**Escenario 1: Pago exitoso**

- **Given:** un socio intenta tomar una clase especial no incluida.
- **When:** el socio realiza el pago en mostrador.
- **Then:** recepción registra el cobro y el sistema habilita el cupo temporalmente.

**Escenario 2: Pago rechazado**

- **Given:** el pago de la clase especial no se procesa correctamente.
- **When:** recepción intenta autorizar el acceso.
- **Then:** el sistema mantiene la restricción y el socio no puede ingresar.

## [US-13] Contratación de Entrenamiento Personal

- **Rol:** Socio
- **Historia:** Como socio, quiero solicitar sesiones de entrenamiento personal, para tener un servicio guiado.

**Criterios de aceptación**

**Escenario 1: Reserva con entrenador**

- **Given:** el socio tiene membresía activa.
- **When:** adquiere un paquete de entrenamiento.
- **Then:** el sistema le habilita el módulo para agendar horarios con el instructor seleccionado.

**Escenario 2: Membresía inactiva**

- **Given:** la membresía del socio está vencida.
- **When:** intenta comprar el paquete de entrenamiento.
- **Then:** el sistema bloquea la compra solicitando renovar primero la membresía.

## [US-14] Validación Integral en Recepción

- **Rol:** Administrador
- **Historia:** Como administrador, quiero que el sistema consolide todas las reglas operativas en la validación de recepción, para evitar accesos inconsistentes.

**Criterios de aceptación**

**Escenario 1: Validación integral**

- **Given:** el socio se presenta en el torniquete/recepción.
- **When:** escanea su acceso.
- **Then:** el sistema valida en menos de 2 segundos vigencia, estatus, clases reservadas y pagos pendientes.

**Escenario 2: Falla de red**

- **Given:** el sistema pierde conexión a internet.
- **When:** el socio escanea su acceso.
- **Then:** el sistema opera en modo local con los últimos datos sincronizados para evitar detener la operación.

> **Implementación:** E1 implementado (vigencia + estatus + clases reservadas del día, con prueba de tiempo < 2 s; los *pagos pendientes* se representan con la suspensión de la membresía, US-06). E2 (modo local sin internet) requiere un cliente de torniquete con caché y queda fuera de la API: ver ADR 0009.

## [US-15] Oferta de Lugares Vacíos en Tiempo Real

- **Rol:** Recepción
- **Historia:** Como recepción, quiero identificar fácilmente los lugares vacíos en tiempo real, para ofrecerlos a socios que llegan sin reserva.

**Criterios de aceptación**

**Escenario 1: Oferta de cupo sobrante**

- **Given:** una clase está por iniciar y aún hay capacidad no reservada.
- **When:** un socio presencial pregunta por disponibilidad.
- **Then:** el sistema muestra el aforo exacto y permite registrarlo manualmente en el momento.

**Escenario 2: Clase saturada**

- **Given:** la clase tiene 100% de asistencia confirmada.
- **When:** el socio presencial pide ingresar.
- **Then:** el sistema impide sobrepasar la capacidad máxima establecida.
