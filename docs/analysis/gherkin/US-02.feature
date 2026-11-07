# language: en
@US-02
Feature: [US-02] Reservación de Clase Específica
  Como socio
  quiero reservar un lugar en una clase específica
  para asegurar mi participación antes de que se llene.

  @E1
  Scenario: Reserva confirmada
    Given una clase tiene lugares disponibles bajo su capacidad máxima.
    When el socio confirma la reservación.
    Then el sistema le asigna el lugar y reduce en 1 el cupo disponible.

  @E2
  Scenario: Restricción por plan
    Given la clase solicitada no está incluida en el plan del socio.
    When intenta reservar la clase.
    Then el sistema bloquea la reserva y notifica que requiere un pago adicional.
