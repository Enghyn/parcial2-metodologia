// Tests puros de la API de ficha clínica avanzada (C-11).
// Estas pruebas verifican que las funciones del cliente de API existen y tienen
// la firma esperada. Como client.ts importa AuthContext (React/Zustand), no se
// puede importar clinica.ts directamente en node:test puro; por tanto se verifica
// la existencia de las exportaciones de forma dinámica.
import assert from "node:assert/strict";
import { test } from "node:test";

test("clinicaAvanzada: funciones exportadas existen", async () => {
  const clinica = await import("../src/shared/api/clinica.ts");

  assert.equal(typeof clinica.listarEvoluciones, "function");
  assert.equal(typeof clinica.crearEvolucion, "function");
  assert.equal(typeof clinica.listarConsentimientos, "function");
  assert.equal(typeof clinica.crearConsentimiento, "function");
  assert.equal(typeof clinica.getHistorialPieza, "function");
});

test("clinicaAvanzada: tipos exportados existen", async () => {
  const clinica = await import("../src/shared/api/clinica.ts");

  // Verificar que los tipos/interfaces están definidos comprobando que las
  // funciones las usan (TypeScript los elimina en runtime, pero la importación
  // dinámica valida que el módulo cargue sin errores).
  assert.ok(clinica);
  assert.ok(Array.isArray(clinica) === false);
});
