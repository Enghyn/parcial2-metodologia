# Modelo de Datos

## Modelo Relacional Simplificado

El esquema está diseñado para un consultorio odontológico moderno (2 a 3 sillones físicos), eliminando complejidad innecesaria de multi-inquilinos (multi-tenancy) y restricciones propietarias de bases de datos.

### Diagrama Entidad-Relación (ERD)

```
[Usuario] 1 ──────── 0..1 [Profesional]
   │
   │ registra
   ▼
[MovimientoCaja] 0..* ──── 0..1 [Turno]
                                  │
                                  ├────── *..1 [Sillon]
                                  ├────── *..1 [Profesional]
                                  └────── *..1 [Paciente]
                                                    │
                                                    ▼
                                            [Odontograma] 1 ──── * [HallazgoPieza]
```

---

## Entidades y Atributos

### 1. `Usuario`
Usuarios internos del sistema (personal de la clínica):
* `id: UUID` (PK)
* `nombre: String(100)`
* `email: String(150)` (UNIQUE)
* `password_hash: String(255)`
* `rol: Enum('admin', 'recepcion', 'odontologo')`
* `activo: Boolean` (Default True)
* `created_at, updated_at: Timestamp`

### 2. `Sillon`
Capacidad física del consultorio (los 2 o 3 sillones de atención):
* `id: UUID` (PK)
* `nombre: String(50)` (Ej: "Sillón 1 - Principal", "Sillón 2", "Sillón 3")
* `descripcion: String(255)` (Opcional)
* `activo: Boolean` (Default True)

### 3. `Profesional`
Odontólogos que atienden en el consultorio:
* `id: UUID` (PK)
* `usuario_id: UUID` (FK opcional → `Usuario.id`)
* `nombre: String(100)`
* `matricula: String(50)`
* `especialidad: String(100)` (Ej: "Odontología General", "Ortodoncia", "Endodoncia")
* `duracion_default_min: Integer` (Default 30)
* `activo: Boolean` (Default True)

### 4. `Paciente`
Ficha de datos básicos de los pacientes:
* `id: UUID` (PK)
* `nombre: String(100)`
* `dni: String(20)` (UNIQUE)
* `telefono: String(30)` (Contacto para turnos y enlaces WhatsApp)
* `email: String(150)` (Opcional)
* `obra_social: String(100)` (Opcional)
* `nro_afiliado: String(50)` (Opcional)
* `activo: Boolean` (Default True)
* `created_at, updated_at: Timestamp`

### 5. `Turno`
Registro de citas con duración variable y asignación física:
* `id: UUID` (PK)
* `paciente_id: UUID` (FK → `Paciente.id`)
* `profesional_id: UUID` (FK → `Profesional.id`)
* `sillon_id: UUID` (FK → `Sillon.id`)
* `prestacion: String(150)` (Ej: "Consulta diagnóstica", "Limpieza", "Extracción")
* `inicio: Timestamp with Timezone`
* `fin: Timestamp with Timezone` (calculado a partir de inicio + duración)
* `duracion_min: Integer`
* `estado: Enum('reservado', 'confirmado', 'presente', 'atendido', 'cancelado')`
* `token_publico: UUID` (UNIQUE, para acceso seguro desde el portal público)
* `sena_monto: Numeric(10, 2)` (Default 0.0)
* `notas: Text` (Opcional)
* `created_at, updated_at: Timestamp`

### 6. `Bloqueo`
Bloqueos temporales de disponibilidad (vacaciones, mantenimiento de sillón, feriados):
* `id: UUID` (PK)
* `sillon_id: UUID` (FK opcional → `Sillon.id`)
* `profesional_id: UUID` (FK opcional → `Profesional.id`)
* `desde: Timestamp with Timezone`
* `hasta: Timestamp with Timezone`
* `motivo: String(255)`

### 7. `Odontograma` y `HallazgoPieza`
Representación esquemática de la dentadura del paciente:
* **`Odontograma`** (Cabecera por paciente):
  * `id: UUID` (PK)
  * `paciente_id: UUID` (FK UNIQUE → `Paciente.id`)
  * `observaciones_generales: Text`
  * `updated_at: Timestamp`
* **`HallazgoPieza`** (Detalle por pieza dental):
  * `id: UUID` (PK)
  * `odontograma_id: UUID` (FK → `Odontograma.id`)
  * `pieza: Integer` (Número FDI de 11 a 48, correspondiente a los 32 dientes permanentes)
  * `estado: Enum('sano', 'caries', 'obturacion', 'corona', 'extraccion', 'tratamiento_conducto')`
  * `observacion: String(255)` (Opcional)
  * `fecha: Date`

### 8. `MovimientoCaja`
Libro diario de ingresos y egresos:
* `id: UUID` (PK)
* `fecha: Timestamp with Timezone` (Default `now()`)
* `tipo: Enum('ingreso', 'egreso')`
* `medio_pago: Enum('efectivo', 'transferencia', 'debito', 'credito', 'otro')`
* `monto: Numeric(10, 2)`
* `concepto: String(255)` (Ej: "Cobro turno - Limpieza dental", "Seña de reserva", "Compra insumos descartables")
* `turno_id: UUID` (FK opcional → `Turno.id`)
* `usuario_id: UUID` (FK → `Usuario.id`, personal que registró el movimiento)

---

## Índices y Reglas de Integridad

1. **Agenda y Búsqueda Rápida de Huecos:**
   * Índices en `Turno(sillon_id, inicio, fin)` y `Turno(profesional_id, inicio, fin)`.
   * Índice en `Turno(token_publico)` para acceso seguro desde `/p/turno/:token`.
2. **Pacientes:**
   * Índice único en `Paciente(dni)`.
3. **Manejo de Borrado Lógico:**
   * Campos `deleted_at: Timestamp?` en tablas de negocio (`Paciente`, `Turno`, `Profesional`, `Sillon`) para preservar historial y permitir recuperación administrativa.

---

## Datos Semilla Iniciales (Seed)

* **Sillones:**
  * Sillón 1 (Box Principal)
  * Sillón 2 (Box Secundario)
  * Sillón 3 (Box Quirúrgico / Endodoncia)
* **Usuarios:**
  * 1 Administrador (`admin@consultorio.com`)
  * 1 Recepcionista (`recepcion@consultorio.com`)
  * 2 Odontólogos (`dr.perez@consultorio.com`, `dra.gomez@consultorio.com`)
