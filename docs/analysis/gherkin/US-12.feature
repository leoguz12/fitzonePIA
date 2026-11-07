# language: en
@US-12
Feature: [US-12] Cobro de Clases Fuera de Plan
  Como recepción
  quiero procesar pagos de clases fuera de plan
  para autorizar el acceso a servicios exclusivos.

  @E1
  Scenario: Pago exitoso
    Given un socio intenta tomar una clase especial no incluida.
    When el socio realiza el pago en mostrador.
    Then recepción registra el cobro y el sistema habilita el cupo temporalmente.

  @E2
  Scenario: Pago rechazado
    Given el pago de la clase especial no se procesa correctamente.
    When recepción intenta autorizar el acceso.
    Then el sistema mantiene la restricción y el socio no puede ingresar.
