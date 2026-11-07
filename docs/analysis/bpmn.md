# BPMN y su relación con el sistema

El diagrama BPMN completo (carriles Socio, Administrador, Recepción e Instructor) está en
[`BPMN_FitZone.pdf`](BPMN_FitZone.pdf). Cada tarea y decisión del proceso corresponde a una operación del sistema:

| Carril | Tarea / decisión del BPMN | Implementación |
|---|---|---|
| Socio | Solicita reserva de clase | `POST /clases/{id}/reservas` → `ReservaAppService.reservar` |
| Administrador/Sistema | Valida vigencia de membresía · ¿Membresía activa y sin suspensión? | `acceso_permitido()` (Specification) |
| Administrador/Sistema | Arroja alerta roja | `403` con `alerta: "ROJA"` (`POST /accesos`) / `403 ACCESO_DENEGADO` (reserva) |
| Administrador/Sistema | Verifica si la clase está en el plan · ¿Plan lo incluye? | `PlanIncluyeServicio` |
| Recepción | Solicita pago adicional · ¿Socio realiza pago? | `402 REQUIERE_PAGO_ADICIONAL` → `POST /clases/{id}/pagos-fuera-de-plan` |
| Recepción | Registra cobro exitoso / Bloquea reserva | `Pago` aprobado / `402 PAGO_RECHAZADO` |
| Administrador/Sistema | Verifica aforo · ¿Clase llena? | `ClaseConCupo` |
| Administrador/Sistema | Agrega a Socio a Lista de Espera | `ClaseEspecial.unirse_lista_espera` → `202` |
| Administrador/Sistema | Confirma reservación | `ClaseEspecial.reservar` → `201` |
| Recepción | Escanea identificación del socio | `POST /accesos` |
| Recepción | Permite acceso y registra entrada | `AccesoPermitido` → tabla `accesos` |
| Recepción | ¿Llega dentro del tiempo de tolerancia? | `POST /clases/{id}/asistencias` (`DentroDeTolerancia`) |
| Sistema | Etiqueta reserva como No-Show | `ClaseEspecial._marcar_no_show` → `NoShowRegistrado` |
| Sistema | Asigna espacio al 1ro en Lista de Espera | `LugarLiberado` → `asignar_vacante` |
| Instructor | Consulta aforo desde su panel | `GET /instructores/{id}/clases`, `GET /clases/{id}/aforo` |
| Instructor | ¿Ocurre imprevisto? · Cancela la sesión | `POST /clases/{id}/cancelacion` |
| Sistema | Envía notificaciones a socios inscritos | `ClaseCancelada` → tabla `notificaciones` |

Los diagramas de secuencia de la Fase 2 están en `docs/architecture/diagramas_fase2/`; las versiones actualizadas al código
final están en [`docs/architecture/arquitectura.md`](../architecture/arquitectura.md).
