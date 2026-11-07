"""Genera docs/traceability.md: Historia de usuario -> Gherkin -> código -> pruebas.

Lee los marcadores ``@pytest.mark.us("US-02", "E1")`` de las pruebas con ``ast``,
así que la matriz refleja las pruebas que de verdad existen.
Uso:  python scripts/trazabilidad.py
"""
import ast
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# US -> (título, rol, caso de uso, componentes de código, ADRs, escenarios Gherkin)
HISTORIAS = {
    "US-01": ("Identificación y acceso en recepción", "Socio", "CU-01",
              "`Membresia.validar_acceso`, `MembresiaVigente`, `MembresiaNoSuspendida`, `AccesoAppService`, `POST /accesos`",
              "0001, 0005", {"E1": "Acceso exitoso", "E2": "Membresía vencida"}),
    "US-02": ("Reservación de clase específica", "Socio", "CU-02",
              "`ClaseEspecial.reservar`, `solicitar_lugar`, `PlanIncluyeServicio`, `ReservaAppService`, `POST /clases/{id}/reservas`",
              "0001, 0002, 0005", {"E1": "Reserva confirmada", "E2": "Restricción por plan"}),
    "US-03": ("Ingreso a lista de espera", "Socio", "CU-03",
              "`ListaEspera`, `ClaseEspecial.unirse_lista_espera`, `abandonar_lista_espera`, `DELETE /clases/{id}/lista-espera/{socio}`",
              "0001, 0007", {"E1": "Ingreso a lista", "E2": "Abandono de lista"}),
    "US-04": ("Cancelación de reservación", "Socio", "CU-02 (flujo de cancelación)",
              "`CancelacionATiempo`, `ClaseEspecial.cancelar_reserva`, evento `CancelacionTardiaRegistrada`, `DELETE /clases/{id}/reservas/{reserva}`",
              "0002, 0005, 0007", {"E1": "Cancelación a tiempo", "E2": "Cancelación tardía"}),
    "US-05": ("Asignación automática desde lista de espera", "Administrador", "CU-03",
              "`ListaEsperaAppService.asignar_vacante`, evento `LugarLiberado`, `ClaseEspecial.asignar_desde_lista_espera`, `GET /clases`",
              "0002, 0007", {"E1": "Asignación automática", "E2": "Lista de espera vacía"}),
    "US-06": ("Bloqueo por cuentas suspendidas", "Recepción", "CU-01",
              "`MEMBRESIA_FSM`, `Membresia.suspender/reactivar`, `POST/DELETE /socios/{id}/suspension`",
              "0001, 0006", {"E1": "Bloqueo por suspensión", "E2": "Regularización"}),
    "US-07": ("Registro automático de No-Shows", "Administrador", "Flujo interno (BPMN: tolerancia)",
              "`DentroDeTolerancia`, `ClaseEspecial.procesar_no_shows/registrar_asistencia`, evento `NoShowRegistrado`, `POST /clases/{id}/no-shows`",
              "0005, 0007", {"E1": "Etiquetado de No-Show", "E2": "Asistencia tardía"}),
    "US-08": ("Consulta de aforo por instructor", "Instructor", "Flujo de lectura",
              "`ConsultasAppService.consultar_aforo`, `SqlReadModel.aforo`, `GET /clases/{id}/aforo`, `GET /instructores/{id}/clases`",
              "0003", {"E1": "Consulta de aforo", "E2": "Clase sin reservas"}),
    "US-09": ("Cancelación de sesión por instructor", "Instructor", "Flujo de excepción",
              "`ClaseEspecial.cancelar_sesion/asignar_suplente`, `puede_gestionar_sesion` (OR), eventos `ClaseCancelada`, `InstructorSuplenteAsignado`",
              "0005, 0007", {"E1": "Cancelación notificada", "E2": "Instructor suplente"}),
    "US-10": ("Reportes de demanda de clases", "Administrador", "Flujo de lectura",
              "`SqlReadModel.reporte_demanda`, `GET /reportes/demanda`", "0003",
              {"E1": "Generación de reporte", "E2": "Filtro por fechas"}),
    "US-11": ("Adquisición de plan trimestral", "Socio", "Gestión de membresías",
              "`Vigencia.desde`, `Membresia.nueva/mejorar_plan/renovar`, `MembresiaAppService`, `POST /socios/{id}/membresia[/mejora]`",
              "0001, 0002", {"E1": "Alta trimestral", "E2": "Upgrade de membresía"}),
    "US-12": ("Cobro de clases fuera de plan", "Recepción", "CU-04",
              "`ejecutar_con_cobro` (compensación), `Pago`, `PasarelaSimulada`, `POST /clases/{id}/pagos-fuera-de-plan`",
              "0002, 0008", {"E1": "Pago exitoso", "E2": "Pago rechazado"}),
    "US-13": ("Contratación de entrenamiento personal", "Socio", "Servicio adicional",
              "`PaqueteEntrenamiento`, `validar_membresia_para_paquete`, `EntrenamientoAppService`, `POST /socios/{id}/entrenamiento-personal`",
              "0001, 0002", {"E1": "Reserva con entrenador", "E2": "Membresía inactiva"}),
    "US-14": ("Validación integral en recepción", "Administrador", "CU-01",
              "`acceso_permitido()` (Specification compuesta), `AccesoAppService`, `reservas_del_dia`, `POST /accesos`",
              "0005, 0009", {"E1": "Validación integral (<2 s)", "E2": "Falla de red (modo local)"}),
    "US-15": ("Oferta de lugares vacíos en tiempo real", "Recepción", "CU-02/CU-03",
              "`SqlReadModel.aforo`, `CAPACIDAD_EXCEDIDA` (invariante), `GET /clases/{id}/aforo`, `POST /clases/{id}/reservas`",
              "0001, 0003", {"E1": "Oferta de cupo sobrante", "E2": "Clase saturada"}),
}
NO_IMPLEMENTADO = {("US-14", "E2"): "Fuera del alcance de la API: requiere un cliente de torniquete con caché local (ADR 0009)"}


def recolectar():
    pruebas = defaultdict(list)
    for archivo in sorted((RAIZ / "tests").rglob("test_*.py")):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef) and nodo.name.startswith("test_"):
                for dec in nodo.decorator_list:
                    if isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") == "us":
                        us, esc = (a.value for a in dec.args[:2])
                        pruebas[(us, esc)].append(f"`{archivo.relative_to(RAIZ / 'tests')}::{nodo.name}`")
    return pruebas


def main():
    pruebas = recolectar()
    filas, cubiertos, total = [], 0, 0
    for us, (titulo, rol, cu, codigo, adrs, escenarios) in HISTORIAS.items():
        for esc, nombre in escenarios.items():
            total += 1
            tests = pruebas.get((us, esc), [])
            if tests:
                cubiertos += 1
                resultado = "<br>".join(tests)
            else:
                resultado = f"⚠️ {NO_IMPLEMENTADO.get((us, esc), 'Sin prueba')}"
            filas.append(f"| {us} | {titulo} ({rol}) | {esc}: {nombre} | {cu} | {codigo} | ADR {adrs} | {resultado} |")
    salida = [
        "# Matriz de trazabilidad\n",
        "> Archivo **generado** por `scripts/trazabilidad.py`. Las pruebas se enlazan con "
        "`@pytest.mark.us(\"US-XX\", \"EY\")`; para regenerar: `python scripts/trazabilidad.py`.\n",
        f"**Escenarios Gherkin con prueba automatizada: {cubiertos} de {total}.**\n",
        "Cadena completa: *BRD → Historia de usuario → Escenario Gherkin → Caso de uso → Modelo de dominio / código → Prueba*.\n",
        "| US | Historia (rol) | Escenario Gherkin | Caso de uso / BPMN | Código que lo implementa | Decisión | Prueba(s) |",
        "|---|---|---|---|---|---|---|",
        *filas, "",
    ]
    destino = RAIZ / "docs" / "traceability.md"
    destino.write_text("\n".join(salida), encoding="utf-8")
    print(f"{cubiertos}/{total} escenarios cubiertos -> {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
