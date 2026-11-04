# Spec Delta — internal-agenda (timezone hardening)

## ADDED Requirements

### Requirement: Horarios de la agenda en ART

La SPA SHALL mostrar el inicio y el fin de cada turno en `America/Argentina/Buenos_Aires`, independientemente de la zona horaria configurada en el navegador del usuario, y SHALL construir el día seleccionado con el mismo criterio.

#### Scenario: Turno de las 09:00 ART

- **WHEN** el backend devuelve un turno con `inicio = 2027-01-10T12:00:00Z`
- **THEN** la agenda interna muestra `09:00` en el bloque del turno

#### Scenario: Navegador en otra zona

- **WHEN** el navegador está configurado en UTC o en otra zona
- **THEN** la agenda sigue mostrando la hora ART del consultorio

#### Scenario: Fecha seleccionada en ART

- **WHEN** el usuario abre la agenda y navega al día siguiente
- **THEN** la fecha consultada corresponde al calendario ART, no al día UTC
