# language: en
@US-15
Feature: [US-15] Oferta de Lugares Vacíos en Tiempo Real
  Como recepción
  quiero identificar fácilmente los lugares vacíos en tiempo real
  para ofrecerlos a socios que llegan sin reserva.

  @E1
  Scenario: Oferta de cupo sobrante
    Given una clase está por iniciar y aún hay capacidad no reservada.
    When un socio presencial pregunta por disponibilidad.
    Then el sistema muestra el aforo exacto y permite registrarlo manualmente en el momento.

  @E2
  Scenario: Clase saturada
    Given la clase tiene 100% de asistencia confirmada.
    When el socio presencial pide ingresar.
    Then el sistema impide sobrepasar la capacidad máxima establecida.
