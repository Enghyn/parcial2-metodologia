import assert from "node:assert/strict";
import { test } from "node:test";

import { CUADRANTES_FDI, PIEZAS_FDI } from "../src/features/clinica/piezas.ts";

test("hay 32 piezas FDI únicas en 4 cuadrantes", () => {
  assert.equal(CUADRANTES_FDI.length, 4);
  assert.equal(PIEZAS_FDI.length, 32);
  assert.equal(new Set(PIEZAS_FDI).size, 32);
  for (const cuadrante of CUADRANTES_FDI) {
    assert.equal(cuadrante.piezas.length, 8);
  }
});

test("no incluye piezas fuera de la nomenclatura FDI", () => {
  for (const invalida of [10, 19, 20, 29, 30, 39, 40, 49]) {
    assert.equal(PIEZAS_FDI.includes(invalida), false);
  }
  for (const pieza of PIEZAS_FDI) {
    assert.ok(pieza >= 11 && pieza <= 48);
    assert.ok(pieza % 10 >= 1 && pieza % 10 <= 8);
  }
});
