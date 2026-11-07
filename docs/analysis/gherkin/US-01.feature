# language: en
@US-01
Feature: [US-01] Identificación y Acceso en Recepción
  Como socio
  quiero identificarme en recepción
  para poder ingresar a las instalaciones a entrenar.

  @E1
  Scenario: Acceso exitoso
    Given el socio tiene una membresía vigente.
    When presenta su identificación en recepción.
    Then el sistema permite el acceso y registra la entrada.

  @E2
  Scenario: Membresía vencida
    Given la membresía del socio ha superado su fecha de vencimiento.
    When presenta su identificación.
    Then el sistema arroja alerta roja y deniega el paso.
