# Spec Delta — internal-agenda (dominio avanzado)

## ADDED Requirements

### Requirement: Acciones de agenda avanzada

La SPA SHALL ofrecer, para los roles autorizados, la acción de reprogramar un turno y la de marcarlo como `ausente`; SHALL reflejar el nuevo horario o estado sin recargar manualmente y SHALL mostrar el error del backend si la operación falla.

#### Scenario: Reprogramar desde la agenda

- **WHEN** recepción selecciona “Reprogramar”, elige un nuevo horario y confirma
- **THEN** la SPA invoca el endpoint de reprogramación y actualiza el bloque del turno

#### Scenario: Marcar ausente desde la agenda

- **WHEN** un usuario autorizado marca un turno como `ausente`
- **THEN** el bloque se actualiza con el estilo de `ausente`

#### Scenario: Error de reprogramación

- **WHEN** el backend responde 409 por solapamiento
- **THEN** la SPA muestra el mensaje y mantiene el horario original
