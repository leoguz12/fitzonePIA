# ADR 0011: Sin autenticación ni roles de usuario en esta versión

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA (alcance) |

## Contexto
El BRD define cuatro roles (socio, recepción, instructor, administrador) pero no especifica un mecanismo de identidad; el alcance del PIA es la lógica de negocio.

## Alternativas consideradas
JWT con roles (descartado por alcance). Un encabezado `X-Rol` sin verificación (descartado: aparenta seguridad que no existe).

## Decisión
La API es abierta. Las reglas que dependen de **quién** actúa solo existen donde el negocio las define con datos: el instructor titular/suplente para cancelar una sesión (`puede_gestionar_sesion`).

## Consecuencias
- **Positivas:** Menos superficie que mantener; el dominio no mezcla seguridad con reglas.
- **Negativas / riesgos:** No debe exponerse a internet con datos reales sin añadir autenticación y autorización (el siguiente paso natural).

## Trazabilidad
BRD §4 y §7
