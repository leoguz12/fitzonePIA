# language: en
@US-03
Feature: [US-03] Ingreso a Lista de Espera
  Como socio
  quiero anotarme en una lista de espera
  para tener oportunidad de entrar si alguien cancela.

  @E1
  Scenario: Ingreso a lista
    Given la clase alcanzó su capacidad máxima.
    When el socio solicita reservar el horario.
    Then el sistema lo agrega al final de la lista de espera.

  @E2
  Scenario: Abandono de lista
    Given el socio está en la lista de espera.
    When decide que ya no quiere asistir y se retira.
    Then el sistema lo remueve y recorre los lugares subsecuentes.
