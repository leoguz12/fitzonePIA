# FitZone — membresías, control de acceso y reservas de clases

Producto Integrador de Aprendizaje (PIA) · **Componentes de Lógica de Negocios** · UANL FIME

| | |
|---|---|
| **Repositorio** | https://github.com/DenilsonGonzalez07/FitZone_PIA |
| **Sistema desplegado** | _pendiente: pegar aquí la URL pública (Render/Railway) después de desplegar_ |
| **Swagger UI / OpenAPI** | `<URL del sistema>/docs` · `<URL del sistema>/openapi.json` (copia en [`docs/api/openapi.json`](docs/api/openapi.json)) |

**Equipo:** Jorge Antonio Granados de Luca (2151253) · Denilson Misael González Marquez (2148813) · Edgar Leonardo Guzmán Ibarra (2148230)

## ¿Qué hace?

FitZone es un gimnasio con membresías mensuales, trimestrales y anuales, clases especiales con cupo limitado y entrenamiento
personal. El sistema automatiza lo que hoy se hace a mano: **validar el acceso** en recepción, **reservar** clases según el plan,
manejar la **lista de espera** (asignación automática al liberarse un lugar), registrar **no-shows**, cobrar **clases fuera de
plan** y generar **reportes de demanda**.

Se implementa con **DDD** (agregados, value objects, eventos de dominio), patrón **Specification**, **State Machine**
declarativa, **CQRS** (lecturas en SQL), **Unit of Work** y una **API REST** documentada con Swagger.

## Estructura del repositorio

```
FitZone_PIA/
├── docs/
│   ├── BRD.md                    BRD refinado (decisiones sobre las 15 preguntas, KPIs)
│   ├── analysis/                 historias de usuario, 15 archivos Gherkin, glosario, BPMN
│   ├── architecture/             arquitectura, ADRs (12), SOLID, máquinas de estado, diagramas
│   ├── api/openapi.json          especificación OpenAPI exportada del código
│   ├── traceability.md           matriz BRD → historia → Gherkin → código → prueba (generada)
│   └── entregas_previas/         BRD, historias, glosario y diseño de las Unidades 2 y 3
├── src/
│   ├── domain/                   entidades, value objects, agregados, specifications, eventos
│   ├── application/              servicios y casos de uso, consultas CQRS, event bus
│   ├── infrastructure/           repositorios SQLAlchemy, Unit of Work, read model, pasarela
│   └── api/                      controllers/endpoints REST, esquemas, composition root
├── tests/                        unitarias (76) + integración (70)
├── scripts/                      demo.py, export_openapi.py, generar_docs.py, trazabilidad.py
├── .github/workflows/ci.yml      CI/CD (pruebas, Docker Compose, despliegue)
├── docker-compose.yml            DB (PostgreSQL) + App + Tests
├── Dockerfile · render.yaml      imagen multi-etapa y plantilla de despliegue
├── .env.example                  variables de entorno (sin secretos reales)
└── README.md
```

## Cómo ejecutarlo

### Opción A — Docker Compose (recomendada: DB + App + Tests)

Requiere [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env                              # opcional: ya hay valores por defecto
docker compose up --build                         # PostgreSQL + API con datos demo
```

Abre **http://localhost:8000/docs** (Swagger UI). Para correr las pruebas contra PostgreSQL:

```bash
docker compose --profile test run --rm tests
docker compose down -v                            # apagar y borrar datos
```

### Opción B — Local sin Docker (SQLite)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
uvicorn src.api.asgi:app --reload
```

Usa por defecto un archivo SQLite (`fitzone.db`). Con `SEED_DEMO_DATA=true` crea socios, instructores y clases de ejemplo.

### Pruebas

```bash
pytest --cov=src --cov-report=term-missing        # 146 pruebas, cobertura 99 % (mínimo exigido: 80 %)
```

## Demo guiada para la defensa

Con la API corriendo (local, Docker o desplegada):

```bash
python scripts/demo.py                            # http://localhost:8000
python scripts/demo.py https://TU-URL.onrender.com
```

Recorre, con datos propios, las reglas principales y muestra el código HTTP de cada paso: contratar membresía, reservar,
plan que no incluye la clase (402), lista de espera (202), cancelación con **asignación automática**, pago fuera de plan
aprobado/rechazado, suspensión con alerta roja y reporte de demanda. También se puede repetir a mano desde Swagger.

Para demostrar un **No-Show** en vivo, arranca con `TOLERANCIA_MINUTOS=1`, programa una clase que inicie en 2 minutos,
reserva, espera a que pase la tolerancia y llama `POST /clases/{id}/no-shows`.

## Endpoints principales

| Método y ruta | Historia | Resultado |
|---|---|---|
| `POST /socios` · `POST /socios/{id}/membresia` | US-11 | Alta y cobro de plan; vencimiento calculado |
| `POST /socios/{id}/membresia/mejora` | US-11 E2 | Upgrade; vencimiento desde el fin del mes |
| `POST /accesos` | US-01, 06, 14 | `200` permitido · `403` alerta roja con motivo |
| `POST/DELETE /socios/{id}/suspension` | US-06 | Suspender / regularizar |
| `POST /clases/{id}/reservas` | US-02, 03 | `201` confirmada · `202` lista de espera · `402` pago adicional · `403` denegada |
| `DELETE /clases/{id}/reservas/{reserva}` | US-04, 05 | Cancelar (tardía = advertencia) y asignar al primero de la lista |
| `DELETE /clases/{id}/lista-espera/{socio}` | US-03 E2 | Abandonar la lista |
| `POST /clases/{id}/pagos-fuera-de-plan` | US-12 | Cobro en mostrador y cupo habilitado |
| `POST /clases/{id}/asistencias` · `POST /clases/{id}/no-shows` | US-07 | Asistencia o No-Show |
| `GET /clases/{id}/aforo` · `GET /instructores/{id}/clases` | US-08, 15 | Capacidad, inscritos, lista de espera |
| `POST /clases/{id}/cancelacion` · `PUT /clases/{id}/instructor-suplente` | US-09 | Cancelar sesión / asignar suplente |
| `POST /socios/{id}/entrenamiento-personal` | US-13 | Paquete de entrenamiento |
| `GET /reportes/demanda?desde=&hasta=` | US-10 | Ocupación, lugares vacíos, % no-show |

Códigos de error: `402` requiere pago · `403` acceso denegado · `404` no existe · `409` regla de negocio o transición inválida · `422` datos inválidos.

## Calidad y trazabilidad

- **146 pruebas** (76 unitarias del dominio, 70 de integración sobre la API y la base de datos) y **99 % de cobertura**.
- **Trazabilidad:** cada prueba declara qué escenario Gherkin verifica (`@pytest.mark.us("US-02", "E1")`). La matriz
  [`docs/traceability.md`](docs/traceability.md) se genera leyendo esos marcadores: **29 de 30 escenarios** tienen prueba
  automatizada; el restante (US-14 E2, modo offline del torniquete) está justificado en el [ADR 0009](docs/architecture/adr/0009-modo-offline-fuera-de-alcance.md).
- **Arquitectura verificada por pruebas:** `tests/unit/test_arquitectura.py` falla si el dominio o la aplicación importan SQLAlchemy, FastAPI o capas externas.
- **CI/CD** (`.github/workflows/ci.yml`): pruebas con cobertura mínima de 80 %, verificación de que la documentación generada está al día, pruebas en Docker Compose contra PostgreSQL, y despliegue automático a Render si se configura el secreto `RENDER_DEPLOY_HOOK_URL`.

## Variables de entorno (12-Factor)

Toda la configuración sale del entorno; ver [`.env.example`](.env.example). Las reglas de negocio supuestas son configurables:

| Variable | Defecto | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./fitzone.db` | Base de datos (Postgres en Docker/producción) |
| `TOLERANCIA_MINUTOS` | `10` | Tolerancia antes de marcar No-Show |
| `LIMITE_CANCELACION_HORAS` | `2` | Cancelar sin advertencia hasta N horas antes |
| `TARIFA_MENSUAL` / `_TRIMESTRAL` / `_ANUAL` | 600 / 1500 / 5000 | Precios de los planes |
| `TARIFA_SESION_ENTRENAMIENTO` | `300` | Precio por sesión de entrenamiento |
| `SEED_DEMO_DATA` | `false` | Crear datos de ejemplo si la BD está vacía |

## Despliegue

El repositorio incluye `render.yaml` (Blueprint de [Render](https://render.com): Web Service Docker + PostgreSQL). Pasos:
**New + → Blueprint → elegir este repositorio**. Render construye el `Dockerfile` (la última etapa, `runtime`) y expone el
`/health`. Para el despliegue continuo desde GitHub Actions, copia el *Deploy Hook* del servicio y guárdalo como secreto
`RENDER_DEPLOY_HOOK_URL` (*Settings → Secrets and variables → Actions*). Después, pega la URL pública en la tabla de arriba.
Los nombres de plan de Render pueden cambiar: si `free` ya no existe, elige otro en el panel.

## Decisiones, supuestos y límites conocidos

- Las 15 preguntas del BRD de la Unidad 2 no se confirmaron con un stakeholder; el equipo documentó un **supuesto** para cada una ([`docs/BRD.md`](docs/BRD.md) §1) y los valores son configurables.
- La pasarela de pago es **simulada** (rechaza referencias que empiezan con `FAIL`); un fallo después del cobro se compensa con reembolso ([ADR 0008](docs/architecture/adr/0008-compensacion-de-pagos.md)).
- Las notificaciones se **guardan** en el sistema (`GET /socios/{id}/notificaciones`); no se envían correos ni SMS.
- **Sin autenticación ni roles** ([ADR 0011](docs/architecture/adr/0011-sin-autenticacion.md)): no exponer a internet con datos reales sin añadirlas.
- El bloqueo de fila que evita sobre-reservar el último cupo ([ADR 0012](docs/architecture/adr/0012-concurrencia.md)) solo tiene efecto en PostgreSQL.
- Pendiente de implementar: reembolso por clase cancelada, umbral de no-shows para suspender, modo offline del torniquete.

## Documentación

[BRD](docs/BRD.md) · [Historias y Gherkin](docs/analysis/user-stories.md) · [Glosario](docs/analysis/glosario.md) · [BPMN](docs/analysis/bpmn.md) ·
[Arquitectura](docs/architecture/arquitectura.md) · [ADRs](docs/architecture/adr/README.md) · [SOLID](docs/architecture/solid.md) ·
[Máquinas de estado](docs/architecture/state-machines.md) · [Trazabilidad](docs/traceability.md)
