# Spec Delta — public-reservation (timezone hardening)

## ADDED Requirements

### Requirement: Disponibilidad pública en ART

El sistema SHALL generar los slots de `GET /api/v1/public/disponibilidad` en `America/Argentina/Buenos_Aires`, exponerlos como instantes UTC correctos y SHALL omitir los slots cuyo inicio ya pasó.

#### Scenario: Slot de las 09:00 ART

- **WHEN** se consulta disponibilidad para un día con capacidad a las 09:00 ART
- **THEN** el slot se serializa como `12:00:00Z` y el portal lo muestra como `09:00`

#### Scenario: Slot pasado excluido

- **WHEN** se consulta la disponibilidad del día actual después de las 09:00 ART
- **THEN** el slot de las 09:00 no se devuelve

### Requirement: Confirmación pública en ART

La vista `/p/turno/:token` SHALL mostrar la fecha y la hora del turno en `America/Argentina/Buenos_Aires`, independientemente de la zona del navegador.

#### Scenario: Confirmación de las 09:00 ART

- **WHEN** el turno tiene `inicio = 2027-01-10T12:00:00Z`
- **THEN** la confirmación muestra `09:00` y la fecha del 10 de enero de 2027
