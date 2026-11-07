# language: en
@US-11
Feature: [US-11] Adquisición de Plan Trimestral
  Como socio
  quiero comprar un plan trimestral
  para asegurar mi acceso por ese periodo de tiempo.

  @E1
  Scenario: Alta trimestral
    Given un usuario realiza el pago de la cuota trimestral.
    When el sistema registra la transacción de inscripción.
    Then se establece la fecha de vencimiento exactamente a tres meses de la fecha de inicio.

  @E2
  Scenario: Upgrade de membresía
    Given el socio tiene un plan mensual activo y compra el anual.
    When se procesa el pago del nuevo plan.
    Then el sistema recalcula el vencimiento sumando el año a partir del fin del mes actual.
