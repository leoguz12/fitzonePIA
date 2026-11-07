# language: en
@US-04
Feature: [US-04] Cancelación de Reservación
  Como socio
  quiero cancelar mi reservación de clase
  para liberar mi lugar si no podré asistir.

  @E1
  Scenario: Cancelación a tiempo
    Given el socio tiene una reserva activa.
    When cancela su asistencia antes del límite de tiempo.
    Then el sistema libera el lugar para otro socio.

  @E2
  Scenario: Cancelación tardía
    Given el socio cancela fuera del tiempo permitido.
    When procesa la cancelación.
    Then el sistema libera el lugar pero registra una advertencia en el perfil del socio.
