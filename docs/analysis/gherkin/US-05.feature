# language: en
@US-05
Feature: [US-05] Asignación Automática desde Lista de Espera
  Como administrador
  quiero que la lista de espera asigne lugares automáticamente
  para evitar la gestión manual y lugares ociosos.

  @E1
  Scenario: Asignación automática
    Given existe una lista de espera y se libera un lugar.
    When el sistema detecta la vacante.
    Then asigna el espacio automáticamente al primer socio de la lista.

  @E2
  Scenario: Lista de espera vacía
    Given se libera un lugar pero no hay nadie en lista de espera.
    When el sistema procesa la cancelación.
    Then el lugar vuelve a aparecer como disponible en el catálogo general.
