# language: en
@US-06
Feature: [US-06] Bloqueo por Cuentas Suspendidas
  Como recepción
  quiero visualizar alertas de cuentas suspendidas
  para aplicar las restricciones correspondientes.

  @E1
  Scenario: Bloqueo por suspensión
    Given un socio tiene el estatus de membresía "suspendida".
    When solicita acceso en recepción.
    Then el sistema muestra el motivo y bloquea la operación.

  @E2
  Scenario: Regularización
    Given el socio suspendido regulariza su situación.
    When recepción actualiza el estatus a activo.
    Then el sistema restaura los privilegios de reserva y acceso.
