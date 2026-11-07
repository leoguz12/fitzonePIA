# language: en
@US-13
Feature: [US-13] Contratación de Entrenamiento Personal
  Como socio
  quiero solicitar sesiones de entrenamiento personal
  para tener un servicio guiado.

  @E1
  Scenario: Reserva con entrenador
    Given el socio tiene membresía activa.
    When adquiere un paquete de entrenamiento.
    Then el sistema le habilita el módulo para agendar horarios con el instructor seleccionado.

  @E2
  Scenario: Membresía inactiva
    Given la membresía del socio está vencida.
    When intenta comprar el paquete de entrenamiento.
    Then el sistema bloquea la compra solicitando renovar primero la membresía.
