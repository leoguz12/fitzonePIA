"""Genera docs/architecture/state-machines.md DESDE las tablas de transición del código.

Así los diagramas de estados siempre coinciden con la implementación.
Uso:  python scripts/generar_docs.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.domain.clase_especial import CLASE_FSM, RESERVA_FSM, EstadoClase, EstadoReserva  # noqa: E402
from src.domain.membresia import MEMBRESIA_FSM, EstadoMembresia  # noqa: E402
from src.domain.pago import PAGO_FSM, EstadoPago  # noqa: E402

MAQUINAS = [
    ("Membresía (US-01, US-06, US-11)", "src/domain/membresia.py", MEMBRESIA_FSM, EstadoMembresia.ACTIVA,
     "El estado `VENCIDA` se recalcula con la fecha del sistema (`refrescar_estado`)."),
    ("Reserva (US-02, US-04, US-07)", "src/domain/clase_especial.py", RESERVA_FSM, EstadoReserva.CONFIRMADA,
     "Solo una reserva `CONFIRMADA` puede cancelarse, asistir o marcarse como No-Show."),
    ("Clase especial (US-07, US-09)", "src/domain/clase_especial.py", CLASE_FSM, EstadoClase.PROGRAMADA,
     "Una clase cancelada no admite reservas ni lista de espera."),
    ("Pago (US-12)", "src/domain/pago.py", PAGO_FSM, EstadoPago.APROBADO,
     "Un pago aprobado puede reembolsarse (compensación cuando falla la operación posterior)."),
]

partes = ["# Máquinas de estado (State Machine)\n",
          "> Archivo **generado** por `scripts/generar_docs.py` a partir de las tablas de transición del código. "
          "No editar a mano.\n"]
for titulo, archivo, fsm, inicial, nota in MAQUINAS:
    partes.append(f"## {titulo}\n\nDefinida en `{archivo}`. {nota}\n")
    partes.append("```mermaid\n" + fsm.a_mermaid(inicial) + "\n```\n")
    partes.append("| Estado origen | Disparador | Estado destino |\n|---|---|---|")
    for origen, disparador, destino in sorted(fsm.transiciones(), key=lambda t: (t[0].value, t[1])):
        partes.append(f"| {origen.value} | `{disparador}` | {destino.value} |")
    partes.append("")

destino = RAIZ / "docs" / "architecture" / "state-machines.md"
destino.write_text("\n".join(partes), encoding="utf-8")
print(f"Generado {destino.relative_to(RAIZ)}")
