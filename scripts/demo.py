"""Guion de demostración para la defensa: recorre los flujos principales contra una API en ejecución.

Uso:
    python scripts/demo.py                      # http://localhost:8000
    python scripts/demo.py https://tu-app.onrender.com

Solo usa la librería estándar. Crea sus propios datos (no depende de SEED_DEMO_DATA).
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")


def llamar(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def paso(titulo, esperado, metodo, ruta, cuerpo=None, mostrar=None):
    estado, resp = llamar(metodo, ruta, cuerpo)
    marca = "OK " if estado == esperado else "FALLO"
    detalle = ""
    if mostrar and isinstance(resp, dict):
        detalle = "  " + ", ".join(f"{k}={resp.get(k)}" for k in mostrar)
    print(f"[{marca}] {titulo:<62} HTTP {estado}{detalle}")
    if estado != esperado:
        print("       respuesta:", resp)
        sys.exit(1)
    return resp


print(f"== Demo FitZone contra {BASE} ==\n")
hora = datetime.fromisoformat(paso("Health check", 200, "GET", "/health", mostrar=["status", "hora_servidor"])["hora_servidor"])
manana = (hora + timedelta(hours=8)).isoformat(timespec="seconds")

print("\n-- Preparación --")
inst = paso("Registrar instructor", 201, "POST", "/instructores", {"nombre": "Laura Pérez"})["id"]
ana = paso("Registrar socio Ana", 201, "POST", "/socios", {"nombre": "Ana Torres", "email": "ana@fitzone.mx"})["id"]
beto = paso("Registrar socio Beto", 201, "POST", "/socios", {"nombre": "Beto Salinas", "email": "beto@fitzone.mx"})["id"]
carla = paso("Registrar socio Carla", 201, "POST", "/socios", {"nombre": "Carla Núñez", "email": "carla@fitzone.mx"})["id"]
paso("US-11 E1  Ana contrata plan ANUAL (se cobra)", 201, "POST", f"/socios/{ana}/membresia",
     {"tipo": "ANUAL", "referencia_pago": "TARJETA-OK"}, ["estado", "fecha_vencimiento"])
paso("US-11 E1  Beto contrata plan MENSUAL", 201, "POST", f"/socios/{beto}/membresia",
     {"tipo": "MENSUAL", "referencia_pago": "TARJETA-OK"}, ["estado", "fecha_vencimiento"])
paso("US-11 E1  Carla contrata plan TRIMESTRAL", 201, "POST", f"/socios/{carla}/membresia",
     {"tipo": "TRIMESTRAL", "referencia_pago": "TARJETA-OK"}, ["estado", "fecha_vencimiento"])
clase = paso("Programar clase de yoga con capacidad 1", 201, "POST", "/clases", {
    "nombre": "Yoga Demo", "instructor_id": inst, "inicio": manana, "duracion_min": 60, "capacidad": 1,
    "servicio_requerido": "yoga", "precio_extra": "150.00"}, ["capacidad", "cupos_disponibles"])["clase_id"]

print("\n-- Control de acceso --")
paso("US-01 E1  Ana pasa por el torniquete", 200, "POST", "/accesos", {"socio_id": ana}, ["permitido"])

print("\n-- Reservas, plan y lista de espera --")
reserva_ana = paso("US-02 E1  Ana reserva (hay cupo)", 201, "POST", f"/clases/{clase}/reservas",
                   {"socio_id": ana}, ["resultado"])["reserva_id"]
paso("US-02 E2  Beto (plan mensual) no tiene yoga: pago adicional", 402, "POST", f"/clases/{clase}/reservas",
     {"socio_id": beto}, ["codigo", "monto_adicional"])
paso("US-03 E1  Carla reserva con la clase llena: lista de espera", 202, "POST", f"/clases/{clase}/reservas",
     {"socio_id": carla}, ["resultado", "posicion"])
paso("US-15 E2  Aforo: la clase nunca excede su capacidad", 200, "GET", f"/clases/{clase}/aforo",
     mostrar=["capacidad", "inscritos", "en_lista_espera"])

print("\n-- Liberación y asignación automática --")
paso("US-04 E1  Ana cancela a tiempo", 200, "DELETE", f"/clases/{clase}/reservas/{reserva_ana}", mostrar=["tardia"])
paso("US-05 E1  Carla fue asignada automáticamente", 200, "GET", f"/clases/{clase}/aforo",
     mostrar=["inscritos", "en_lista_espera"])
notas = llamar("GET", f"/socios/{carla}/notificaciones")[1]
print("          notificaciones de Carla:", [n["asunto"] for n in notas])

print("\n-- Clase fuera de plan (cobro con pasarela simulada) --")
clase2 = paso("Programar segunda clase de yoga (capacidad 5)", 201, "POST", "/clases", {
    "nombre": "Yoga Demo 2", "instructor_id": inst, "inicio": manana, "duracion_min": 60, "capacidad": 5,
    "servicio_requerido": "yoga", "precio_extra": "150.00"})["clase_id"]
paso("US-12 E2  Pago rechazado: se mantiene la restricción", 402, "POST", f"/clases/{clase2}/pagos-fuera-de-plan",
     {"socio_id": beto, "referencia_pago": "FAIL-TARJETA"}, ["codigo"])
paso("US-12 E1  Pago exitoso: se habilita el lugar", 201, "POST", f"/clases/{clase2}/pagos-fuera-de-plan",
     {"socio_id": beto, "referencia_pago": "TARJETA-OK"}, ["resultado"])

print("\n-- Suspensión --")
paso("US-06 E1  Se suspende a Beto", 200, "POST", f"/socios/{beto}/suspension", {"motivo": "Pago pendiente"}, ["estado"])
paso("US-06 E1  Beto en el torniquete: alerta roja", 403, "POST", "/accesos", {"socio_id": beto}, ["alerta", "codigo"])
paso("US-06 E2  Regularización: se restauran privilegios", 200, "DELETE", f"/socios/{beto}/suspension", mostrar=["estado"])

print("\n-- Reportes (CQRS) --")
hoy = hora.date().isoformat()
r = paso("US-10 E1  Reporte de demanda", 200, "GET", f"/reportes/demanda?desde={hoy}&hasta={(hora + timedelta(days=2)).date().isoformat()}")
print("          resumen:", r["resumen"])
print("\nDemo completa: todos los pasos respondieron como lo define el BRD.")
