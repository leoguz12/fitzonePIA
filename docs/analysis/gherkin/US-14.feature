# language: en
@US-14
Feature: [US-14] Validación Integral en Recepción
  Como administrador
  quiero que el sistema consolide todas las reglas operativas en la validación de recepción
  para evitar accesos inconsistentes.

  @E1
  Scenario: Validación integral
    Given el socio se presenta en el torniquete/recepción.
    When escanea su acceso.
    Then el sistema valida en menos de 2 segundos vigencia, estatus, clases reservadas y pagos pendientes.

  @E2
  Scenario: Falla de red
    Given el sistema pierde conexión a internet.
    When el socio escanea su acceso.
    Then el sistema opera en modo local con los últimos datos sincronizados para evitar detener la operación.
