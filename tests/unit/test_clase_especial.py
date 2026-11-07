from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.domain.clase_especial import (
    ClaseEspecial, EstadoClase, EstadoReserva, ListaEspera, ResultadoAsistencia,
)
from src.domain.errors import BusinessRuleViolation, Forbidden, InvalidData, InvalidTransition, NotFound
from src.domain.events import (
    AsistenciaRegistrada, CancelacionTardiaRegistrada, CapacidadAlcanzada, ClaseCancelada,
    InstructorSuplenteAsignado, LugarLiberado, NoShowRegistrado, ReservaConfirmada,
    SocioAgregadoAListaEspera, SocioAsignadoDesdeEspera,
)
from tests.factories import AHORA, LIMITE_CANCELACION, TOLERANCIA, clase


def tipos(c):
    return [type(e) for e in c.extraer_eventos()]


@pytest.mark.us("US-02", "E1")
def test_reservar_asigna_lugar_y_reduce_cupo_en_uno():
    c = clase(capacidad=3)
    r = c.reservar("s1", AHORA)
    assert r.estado == EstadoReserva.CONFIRMADA
    assert c.cupos_disponibles == 2 and c.ocupados == 1
    assert tipos(c) == [ReservaConfirmada]


def test_invariante_nunca_excede_la_capacidad_ni_reserva_dos_veces():
    c = clase(capacidad=1)
    c.reservar("s1", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        c.reservar("s2", AHORA)
    assert e.value.codigo == "CAPACIDAD_EXCEDIDA"
    with pytest.raises(BusinessRuleViolation) as e:
        c.reservar("s1", AHORA)
    assert e.value.codigo == "RESERVA_DUPLICADA"
    assert c.cupos_disponibles == 0


def test_no_admite_reservas_si_la_clase_esta_cancelada():
    c = clase()
    c.cancelar_sesion("inst-1", "Imprevisto", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        c.reservar("s1", AHORA)
    assert e.value.codigo == "CLASE_NO_DISPONIBLE"
    with pytest.raises(BusinessRuleViolation):
        c.unirse_lista_espera("s1", AHORA)


@pytest.mark.us("US-03", "E1")
def test_clase_llena_agrega_al_final_de_la_lista_de_espera():
    c = clase(capacidad=1)
    c.reservar("s1", AHORA)
    c.extraer_eventos()
    assert c.unirse_lista_espera("s2", AHORA) == 1
    assert c.unirse_lista_espera("s3", AHORA) == 2
    assert c.lista_espera.socios == ["s2", "s3"]
    assert tipos(c).count(CapacidadAlcanzada) == 2 and True


def test_lista_de_espera_requiere_clase_llena_y_sin_duplicados():
    c = clase(capacidad=1)
    with pytest.raises(BusinessRuleViolation) as e:
        c.unirse_lista_espera("s1", AHORA)
    assert e.value.codigo == "CLASE_CON_CUPO"
    c.reservar("s1", AHORA)
    with pytest.raises(BusinessRuleViolation):
        c.unirse_lista_espera("s1", AHORA)  # ya tiene lugar
    c.unirse_lista_espera("s2", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        c.unirse_lista_espera("s2", AHORA)
    assert e.value.codigo == "RESERVA_DUPLICADA"
    with pytest.raises(BusinessRuleViolation) as e:
        c.lista_espera.agregar("s2", AHORA)
    assert e.value.codigo == "YA_EN_LISTA_ESPERA"


@pytest.mark.us("US-03", "E2")
def test_abandonar_lista_recorre_los_lugares_subsecuentes():
    c = clase(capacidad=1)
    c.reservar("s1", AHORA)
    for s in ("s2", "s3", "s4"):
        c.unirse_lista_espera(s, AHORA)
    c.abandonar_lista_espera("s2")
    assert c.lista_espera.posicion_de("s3") == 1 and c.lista_espera.posicion_de("s4") == 2
    with pytest.raises(BusinessRuleViolation) as e:
        c.abandonar_lista_espera("s2")
    assert e.value.codigo == "NO_EN_LISTA_ESPERA"


@pytest.mark.us("US-04", "E1")
def test_cancelacion_a_tiempo_libera_el_lugar_sin_advertencia():
    c = clase()  # inicia en 8 h; el límite es 2 h
    r = c.reservar("s1", AHORA)
    c.extraer_eventos()
    tarde = c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)
    assert tarde is False and r.estado == EstadoReserva.CANCELADA and c.cupos_disponibles == 2
    assert tipos(c) == [LugarLiberado]


@pytest.mark.us("US-04", "E2")
def test_cancelacion_tardia_libera_pero_registra_advertencia():
    c = clase(inicio=AHORA + timedelta(minutes=30))
    r = c.reservar("s1", AHORA)
    c.extraer_eventos()
    assert c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION) is True
    assert r.cancelada_tarde and c.cupos_disponibles == 2
    assert tipos(c) == [LugarLiberado, CancelacionTardiaRegistrada]


def test_cancelar_reserva_casos_invalidos():
    c = clase()
    r = c.reservar("s1", AHORA)
    c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)
    with pytest.raises(InvalidTransition):
        c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)  # ya cancelada
    with pytest.raises(NotFound):
        c.cancelar_reserva("no-existe", AHORA, LIMITE_CANCELACION)
    r2 = c.reservar("s2", AHORA)
    with pytest.raises(BusinessRuleViolation) as e:
        c.cancelar_reserva(r2.id, c.inicio + timedelta(minutes=1), LIMITE_CANCELACION)
    assert e.value.codigo == "CLASE_YA_INICIADA"


@pytest.mark.us("US-05", "E1")
def test_liberar_lugar_asigna_automaticamente_al_primero_de_la_lista():
    c = clase(capacidad=1)
    r = c.reservar("s1", AHORA)
    c.unirse_lista_espera("s2", AHORA); c.unirse_lista_espera("s3", AHORA)
    c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)
    c.extraer_eventos()
    asignadas = c.asignar_desde_lista_espera(AHORA, lambda s: True)
    assert [a.socio_id for a in asignadas] == ["s2"]
    assert c.lista_espera.socios == ["s3"] and c.cupos_disponibles == 0
    assert tipos(c) == [SocioAsignadoDesdeEspera]


@pytest.mark.us("US-05", "E2")
def test_lista_vacia_el_lugar_vuelve_a_estar_disponible():
    c = clase(capacidad=1)
    r = c.reservar("s1", AHORA)
    c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)
    assert c.asignar_desde_lista_espera(AHORA, lambda s: True) == []
    assert c.cupos_disponibles == 1


def test_asignacion_descarta_socios_no_elegibles_y_respeta_estado():
    c = clase(capacidad=1)
    r = c.reservar("s1", AHORA)
    c.unirse_lista_espera("malo", AHORA); c.unirse_lista_espera("bueno", AHORA)
    c.cancelar_reserva(r.id, AHORA, LIMITE_CANCELACION)
    asignadas = c.asignar_desde_lista_espera(AHORA, lambda s: s == "bueno")
    assert [a.socio_id for a in asignadas] == ["bueno"] and len(c.lista_espera) == 0
    cancelada = clase(capacidad=1)
    cancelada.cancelar_sesion("inst-1", "x", AHORA)
    assert cancelada.asignar_desde_lista_espera(AHORA, lambda s: True) == []


@pytest.mark.us("US-07", "E1")
def test_pasada_la_tolerancia_la_reserva_sin_asistencia_es_no_show():
    c = clase()
    r = c.reservar("s1", AHORA)
    c.extraer_eventos()
    assert c.procesar_no_shows(c.inicio + timedelta(minutes=5), TOLERANCIA) == []  # aún en tolerancia
    marcadas = c.procesar_no_shows(c.inicio + timedelta(minutes=11), TOLERANCIA)
    assert [m.id for m in marcadas] == [r.id] and r.estado == EstadoReserva.NO_SHOW
    assert c.estado == EstadoClase.EN_CURSO and c.cupos_disponibles == 2
    assert tipos(c) == [NoShowRegistrado, LugarLiberado]


@pytest.mark.us("US-07", "E2")
def test_llegar_dentro_de_la_tolerancia_valida_asistencia_sin_no_show():
    c = clase()
    c.reservar("s1", AHORA)
    c.extraer_eventos()
    res = c.registrar_asistencia("s1", c.inicio + timedelta(minutes=10), TOLERANCIA)  # límite exacto
    assert res == ResultadoAsistencia.ASISTENCIA_REGISTRADA
    assert tipos(c) == [AsistenciaRegistrada]
    assert c.procesar_no_shows(c.inicio + timedelta(minutes=30), TOLERANCIA) == []


def test_llegar_despues_de_la_tolerancia_es_no_show_y_libera():
    c = clase()
    r = c.reservar("s1", AHORA)
    res = c.registrar_asistencia("s1", c.inicio + timedelta(minutes=11), TOLERANCIA)
    assert res == ResultadoAsistencia.NO_SHOW and r.estado == EstadoReserva.NO_SHOW


def test_asistencia_sin_reserva_o_clase_cancelada_se_rechaza():
    c = clase()
    with pytest.raises(BusinessRuleViolation) as e:
        c.registrar_asistencia("s1", AHORA, TOLERANCIA)
    assert e.value.codigo == "SIN_RESERVA"
    c.cancelar_sesion("inst-1", "x", AHORA)
    with pytest.raises(BusinessRuleViolation):
        c.registrar_asistencia("s1", AHORA, TOLERANCIA)
    assert c.procesar_no_shows(AHORA + timedelta(days=1), TOLERANCIA) == []


@pytest.mark.us("US-09", "E1")
def test_instructor_cancela_sesion_libera_cupos_y_notifica_a_todos():
    c = clase(capacidad=1)
    c.reservar("s1", AHORA); c.unirse_lista_espera("s2", AHORA)
    c.extraer_eventos()
    afectados = c.cancelar_sesion("inst-1", "Enfermedad", AHORA)
    assert set(afectados) == {"s1", "s2"}
    assert c.estado == EstadoClase.CANCELADA and c.cupos_disponibles == 1 and len(c.lista_espera) == 0
    ev = c.extraer_eventos()
    assert isinstance(ev[0], ClaseCancelada) and ev[0].motivo == "Enfermedad"


def test_cancelar_sesion_exige_autoridad_motivo_y_estado():
    c = clase()
    with pytest.raises(Forbidden):
        c.cancelar_sesion("intruso", "x", AHORA)
    with pytest.raises(InvalidData):
        c.cancelar_sesion("inst-1", " ", AHORA)
    c.cancelar_sesion("inst-1", "x", AHORA)
    with pytest.raises(InvalidTransition):
        c.cancelar_sesion("inst-1", "otra vez", AHORA)


@pytest.mark.us("US-09", "E2")
def test_suplente_mantiene_la_clase_activa_y_notifica_el_cambio():
    c = clase()
    c.reservar("s1", AHORA)
    c.extraer_eventos()
    c.asignar_suplente("inst-2", AHORA)
    assert c.estado == EstadoClase.PROGRAMADA and c.instructor_suplente_id == "inst-2"
    ev = c.extraer_eventos()[0]
    assert isinstance(ev, InstructorSuplenteAsignado) and ev.socios_afectados == ("s1",)
    assert c.cancelar_sesion("inst-2", "titular ausente", AHORA)  # el suplente también puede cancelar


def test_suplente_invalido():
    c = clase()
    with pytest.raises(BusinessRuleViolation):
        c.asignar_suplente("inst-1", AHORA)
    c.cancelar_sesion("inst-1", "x", AHORA)
    with pytest.raises(BusinessRuleViolation):
        c.asignar_suplente("inst-2", AHORA)


def test_finalizar_marca_pendientes_como_no_show_sin_liberar():
    c = clase()
    c.reservar("s1", AHORA)
    c.extraer_eventos()
    with pytest.raises(BusinessRuleViolation):
        c.finalizar(c.inicio)
    c.finalizar(c.fin)
    assert c.estado == EstadoClase.FINALIZADA
    assert tipos(c) == [NoShowRegistrado]
    with pytest.raises(BusinessRuleViolation):
        c.registrar_asistencia("s1", c.fin, TOLERANCIA)


@pytest.mark.parametrize("kw", [
    {"nombre": " "}, {"servicio_requerido": ""}, {"duracion_min": 0}, {"precio_extra": Decimal("0")},
])
def test_clase_valida_sus_invariantes(kw):
    base = dict(nombre="Yoga", instructor_id="i", inicio=AHORA, duracion_min=60, capacidad=5,
                servicio_requerido="yoga", precio_extra=Decimal("100"))
    base.update(kw)
    with pytest.raises(InvalidData):
        ClaseEspecial.programar(**base)


def test_lista_espera_extraer_y_vaciar():
    le = ListaEspera()
    assert le.extraer_primero() is None
    le.agregar("a", AHORA); le.agregar("b", AHORA)
    assert le.extraer_primero().socio_id == "a"
    assert le.vaciar() == ["b"] and len(le) == 0
    assert le.retirar("zzz") is False
