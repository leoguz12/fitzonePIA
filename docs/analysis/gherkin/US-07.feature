# language: en
@US-07
Feature: [US-07] Registro Automático de No-Shows
  Como administrador
  quiero registrar de forma automática los no-shows
  para medir la inasistencia y aplicar políticas.

  @E1
  Scenario: Etiquetado de No-Show
    Given la clase ha comenzado y un socio reservó pero no pasó asistencia.
    When transcurre el tiempo de tolerancia.
    Then el sistema etiqueta la reserva como no-show y guarda el registro.

  @E2
  Scenario: Asistencia tardía
    Given el socio llega dentro de los minutos de tolerancia.
    When registra su entrada en recepción.
    Then el sistema valida su asistencia y no genera el reporte de no-show.
