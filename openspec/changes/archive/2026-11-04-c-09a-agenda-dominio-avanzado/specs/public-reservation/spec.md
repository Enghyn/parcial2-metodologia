# Spec Delta — public-reservation (dominio avanzado)

## ADDED Requirements

### Requirement: Ventana mínima de cancelación pública

El sistema SHALL rechazar con 409 la cancelación pública de un turno cuando falte menos que `cancelacion_min_horas` (default 12) para su `inicio`, y SHALL permitir la cancelación dentro de la ventana. La recepción SHALL poder cancelar con override desde la agenda interna.

#### Scenario: Cancelación dentro de la ventana

- **WHEN** el paciente cancela un turno que comienza en 24 h
- **THEN** la API responde 200 y el turno queda `cancelado`

#### Scenario: Cancelación fuera de la ventana

- **WHEN** el paciente cancela un turno que comienza en 2 h
- **THEN** la API responde 409 y el turno no cambia

#### Scenario: Override de recepción

- **WHEN** recepción cancela un turno fuera de la ventana desde la agenda interna
- **THEN** la API permite la cancelación
