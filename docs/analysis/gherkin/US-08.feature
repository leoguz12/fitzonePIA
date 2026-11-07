# language: en
@US-08
Feature: [US-08] Consulta de Aforo por Instructor
  Como instructor
  quiero consultar el horario y el aforo de mis clases
  para preparar la sesión adecuadamente.

  @E1
  Scenario: Consulta de aforo
    Given el instructor accede a su portal de gestión.
    When selecciona la clase del día.
    Then el sistema despliega la capacidad máxima y el número de reservas actuales.

  @E2
  Scenario: Clase sin reservas
    Given la clase programada no tiene ningún socio inscrito.
    When el instructor revisa el horario.
    Then el sistema indica "0 inscritos" y permite gestionar la cancelación preventiva.
