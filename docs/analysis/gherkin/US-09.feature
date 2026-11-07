# language: en
@US-09
Feature: [US-09] Cancelación de Sesión por Instructor
  Como instructor
  quiero cancelar una sesión en el sistema
  para notificar a los alumnos en caso de imprevistos.

  @E1
  Scenario: Cancelación notificada
    Given una clase cuenta con reservaciones activas.
    When el instructor cancela la sesión desde su panel.
    Then el sistema envía notificaciones a los socios inscritos y libera sus cupos.

  @E2
  Scenario: Instructor suplente
    Given el instructor titular no puede asistir pero hay un reemplazo.
    When el administrador asigna al instructor suplente en el sistema.
    Then la clase se mantiene activa y se notifica el cambio de instructor a los socios.
