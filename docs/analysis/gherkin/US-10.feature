# language: en
@US-10
Feature: [US-10] Reportes de Demanda de Clases
  Como administrador
  quiero generar reportes de reservas y asistencias
  para medir la demanda de las clases.

  @E1
  Scenario: Generación de reporte
    Given existen registros históricos de clases impartidas.
    When el administrador solicita el reporte de demanda.
    Then el sistema despliega la tasa de ocupación y los lugares vacíos por clase.

  @E2
  Scenario: Filtro por fechas
    Given el administrador requiere datos específicos.
    When aplica un filtro de fechas para el último mes.
    Then el sistema ajusta las métricas exclusivamente a ese periodo.
