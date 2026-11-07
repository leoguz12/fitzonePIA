# ADR 0010: Contenedores y 12-Factor App

| Campo | Contenido |
|---|---|
| **Estado** | ACEPTADA |

## Contexto
El PIA exige un entorno reproducible (DB + App + Tests), configuración separada del código y despliegue.

## Alternativas consideradas
Instalar todo a mano (descartado: no reproducible). Credenciales en el código (descartado).

## Decisión
`Dockerfile` multi-etapa (test / runtime) y `docker-compose.yml` con `db`, `app` y `tests` (perfil). Toda la configuración en variables de entorno (`.env.example`, sin secretos); `DATABASE_URL` se normaliza para Render. `GET /health` para el *health check*.

## Consecuencias
- **Positivas:** `docker compose up` levanta todo; el mismo contenedor se despliega en Render/Railway.
- **Negativas / riesgos:** La contraseña por defecto de desarrollo (`fitzone_dev`) debe cambiarse en cualquier entorno real.

## Trazabilidad
Calidad y producción (todo el sistema)
