# BRD — Business Requirements Document: FitZone

**Curso:** Componentes de Lógica de Negocios (CLN) · UANL FIME
**Equipo:** Jorge Antonio Granados de Luca (2151253) · Denilson Misael González Marquez (2148813) · Edgar Leonardo Guzmán Ibarra (2148230)
**Versión:** 2.0 (PIA) — refina el BRD de la Unidad 2 (`docs/entregas_previas/U2_BRD_FitZone.pdf`).

> **Qué cambió respecto a la versión U2:** (1) las 15 preguntas al stakeholder tenían una respuesta pendiente; en la sección 1 se
> documenta la **decisión/supuesto** que tomó el equipo para poder implementar, marcada como *por confirmar*; (2) el alcance y
> los requerimientos ahora indican **cómo se verifica** cada uno en el sistema (historia de usuario, endpoint y prueba);
> (3) los KPI indican de dónde se mide cada indicador.

## 1. Preguntas al stakeholder y decisiones adoptadas

Ninguna de las 15 preguntas pudo confirmarse con el negocio antes de implementar. Para no bloquear el desarrollo, cada una
tiene un **supuesto S-xx**. Los valores numéricos son configurables por variables de entorno (`.env.example`), de modo que
cambiar un supuesto no requiere tocar el código.

| # | Pregunta (U2) | Decisión / supuesto del equipo (*por confirmar*) | Dónde vive |
|---|---|---|---|
| P1 | ¿Cuándo inicia la vigencia y a qué hora vence el último día? | **S-01** Inicia en la fecha de contratación (o la fecha indicada). El **último día es válido** (vence al terminar la fecha de vencimiento). | `Vigencia.vigente_en` |
| P2 | ¿Hay periodo de gracia al vencer? | **S-02** No hay periodo de gracia. El día siguiente al vencimiento el acceso se niega. | `MembresiaVigente` |
| P3 | ¿Cómo se determina qué clases incluye cada plan? | **S-03** Catálogo de servicios por plan: Mensual = {funcional}; Trimestral = {funcional, yoga, spinning}; Anual = Trimestral + {crossfit, entrenamiento_personal}. Cada clase indica el `servicio_requerido`. | `SERVICIOS_POR_PLAN` |
| P4 | ¿Anticipación máxima y mínima para reservar? | **S-04** Máxima: sin límite. Mínima: se puede reservar hasta antes de que **inicie** la clase. | `ClaseYaIniciada` |
| P5 | ¿Límite para cancelar sin penalización? | **S-05** **2 horas** antes del inicio (`LIMITE_CANCELACION_HORAS`). Después: se libera el lugar y se registra una advertencia. | `CancelacionATiempo` |
| P6 | ¿Qué penalización hay por no-show? | **S-06** Se libera el lugar y se suma un *no-show* al perfil del socio. No hay bloqueo automático (queda como mejora: umbral de no-shows). | `Socio.registrar_no_show` |
| P7 | ¿Cuánto tiempo tiene el socio de la lista de espera para confirmar? | **S-07** Ninguno: la asignación es **automática e inmediata** (KPI del BRD: "inmediato al cancelar"). Se descarta a quien ya no cumpla las reglas. | `asignar_desde_lista_espera` |
| P8 | ¿Cuándo puede recepción saltarse una restricción? | **S-08** Nunca (restricción del BRD §7). No existe un endpoint de "ingreso manual forzado". | — |
| P9 | ¿Qué ve el instructor de sus alumnos? | **S-09** Capacidad, inscritos, cupos disponibles, lista de espera, asistencias y no-shows de cada clase. | `GET /clases/{id}/aforo` |
| P10 | ¿Protocolo y límite para que el instructor cancele? | **S-10** Hasta antes de que inicie la clase, con **motivo obligatorio**; solo el instructor titular o su suplente. | `puede_gestionar_sesion` |
| P11 | ¿Cómo se compensa al socio si el instructor cancela? | **S-11** Se liberan sus cupos y se le notifica. La compensación económica (reembolso de clases pagadas fuera de plan) **no está implementada** (mejora futura). | `ClaseCancelada` |
| P12 | ¿Cómo se procesa el pago de una clase fuera de plan? | **S-12** Recepción cobra en mostrador; se crea un `Pago` asociado a la reserva. Solo se cobra si hay lugar disponible. Si el registro falla después del cobro, se **reembolsa** automáticamente. | `ejecutar_con_cobro` |
| P13 | ¿Qué KPIs revisa el administrador? | **S-13** Tasa de ocupación, lugares vacíos, % de no-shows, por clase y por periodo. | `GET /reportes/demanda` |
| P14 | ¿Motivos de suspensión y quién la autoriza? | **S-14** La suspende recepción o el administrador con un **motivo obligatorio** (ej. pago pendiente). | `Membresia.suspender` |
| P15 | ¿Qué queda fuera del alcance? | **S-15** Nómina, mantenimiento, marketing (U2) + reembolsos por clase cancelada, notificaciones reales por correo/SMS y modo offline del torniquete. | §5 |

## 2. Contexto del negocio

FitZone vende membresías mensuales, trimestrales y anuales, además de entrenamiento personal y clases especiales. Los servicios
y accesos permitidos dependen estrictamente del plan contratado. Hoy el control de acceso, las reservaciones y las listas de
espera operan con controles manuales y reglas inconsistentes.

## 3. Problema / oportunidad

| Problema | Efecto |
|---|---|
| **Lugares vacíos:** alta incidencia de no-shows | Se quita el lugar a socios que sí asistirían |
| **Ineficiencia operativa:** lista de espera manual | Reasignación lenta de espacios |
| **Inconsistencia en accesos:** sin validación automática de membresía | Accesos erróneos |
| **Falta de métricas:** no se mide la demanda real | Horarios sin sustento |

**Oportunidad:** un sistema centralizado que automatice reglas de membresía, control de accesos y flujo de reservaciones;
asigne lugares de lista de espera en tiempo real; controle los no-shows; y genere reportes de ocupación.

## 4. Stakeholders

| Rol | Responsabilidad en el proceso | Endpoints principales |
|---|---|---|
| **Socio** | Contrata planes; reserva, asiste o cancela; se identifica en recepción | `/socios`, `/clases/{id}/reservas` |
| **Recepción** | Valida identidad y vigencia; cobra clases fuera de plan | `/accesos`, `/clases/{id}/pagos-fuera-de-plan` |
| **Instructor** | Revisa horarios y aforo; cancela sesiones | `/instructores/{id}/clases`, `/clases/{id}/cancelacion` |
| **Administrador** | Mide demanda; supervisa asignación; define políticas; asigna suplentes | `/reportes/demanda`, `/clases/{id}/instructor-suplente` |

## 5. Alcance

**Dentro del alcance (implementado):** gestión de membresías (inicio, vencimiento, estatus activa/vencida/suspendida) ·
control de accesos en recepción · reservación con descuento de cupo, cancelación y lista de espera automática ·
excepciones (no-shows, clases fuera de plan, cancelaciones del instructor, suplentes) · entrenamiento personal ·
reportes de demanda · pagos simulados con compensación.

**Fuera de alcance:** nómina y comisiones de instructores · mantenimiento del equipo · campañas de marketing ·
reembolso económico por clases canceladas · envío real de correo/SMS (las notificaciones se guardan en el sistema) ·
modo offline del torniquete (ADR 0009) · autenticación y roles de usuario (ADR 0010).

## 6. Necesidades del negocio y requerimientos funcionales

| ID | Requerimiento | Historias | Verificación |
|---|---|---|---|
| RF-01 | **Gestión de membresías:** registrar fecha de inicio y calcular el vencimiento según el plan | US-11 | `Vigencia.desde`, pruebas `US-11` |
| RF-02 | **Políticas de acceso:** identificar estatus vencidos o suspendidos, negando acceso o reserva | US-01, US-06, US-14 | `acceso_permitido()`, pruebas `US-01/06/14` |
| RF-03 | **Control de aforo:** límite de capacidad; al llenarse, habilitar lista de espera | US-02, US-03, US-15 | invariante `cupos >= 0`, pruebas `US-02/03/15` |
| RF-04 | **Liberación de espacios:** una cancelación asigna de inmediato al primero de la lista | US-04, US-05 | evento `LugarLiberado`, pruebas `US-04/05` |
| RF-05 | **Manejo de excepciones:** cobro de clases fuera de plan; aviso de cancelación del instructor; no-shows | US-07, US-09, US-12 | pruebas `US-07/09/12` |
| RF-06 | **Entrenamiento personal** sujeto a membresía vigente | US-13 | `PaqueteEntrenamiento`, pruebas `US-13` |
| RF-07 | **Métricas de demanda** en línea | US-08, US-10 | `GET /reportes/demanda`, pruebas `US-10` |

Detalle por escenario: [`docs/traceability.md`](traceability.md).

## 7. Restricciones y supuestos

- **Restricciones:** recepción no puede saltarse las validaciones de acceso sin autorización; el cupo de una clase **nunca** puede excederse (seguridad y espacio físico).
- **Supuestos:** los socios cuentan con un medio de identificación vinculable a su perfil (en el sistema, el `socio_id`); los instructores tienen una interfaz para gestionar sus horarios; los pagos se procesan con una pasarela externa (simulada en este proyecto).

## 8. Criterios de éxito (KPI) y cómo se miden

| Indicador | Estado actual | Meta comprometida | Cómo lo mide el sistema |
|---|---|---|---|
| Tiempo de asignación de lista de espera | Manual, lento, propenso a errores | Automático, inmediato al cancelar | La asignación ocurre en la misma petición de cancelación (`LugarLiberado` → `asignar_vacante`) |
| Inconsistencias de acceso por membresía | Frecuentes (revisión manual) | 0 % (bloqueo automático) | `POST /accesos` aplica siempre la misma política; historial en `GET /socios/{id}/accesos` |
| % de lugares vacíos por no-shows | Alto, sin medición | < 5 % | `tasa_no_show` en `GET /reportes/demanda` |
| Reporte de demanda | Difícil y laborioso | En línea, en tiempo real | `GET /reportes/demanda?desde=&hasta=` |
| Validación en recepción | Lenta | < 2 segundos | Prueba automatizada `US-14 E1` |

## 9. Parámetros configurables (12-Factor)

| Variable | Valor por defecto | Significado |
|---|---|---|
| `TOLERANCIA_MINUTOS` | 10 | Minutos después del inicio antes de marcar No-Show (S-06) |
| `LIMITE_CANCELACION_HORAS` | 2 | Horas antes del inicio para cancelar sin advertencia (S-05) |
| `TARIFA_MENSUAL` / `TRIMESTRAL` / `ANUAL` | 600 / 1500 / 5000 MXN | Precio de cada plan (supuesto) |
| `TARIFA_SESION_ENTRENAMIENTO` | 300 MXN | Precio por sesión de entrenamiento personal (supuesto) |
