import assert from "node:assert/strict";
import { test } from "node:test";

import { construirQueryTurnos, rutaTurnos } from "../src/shared/api/turnosQuery.ts";

test("rango completo arma desde y hasta", () => {
  assert.equal(
    construirQueryTurnos({ desde: "2027-01-04", hasta: "2027-01-10" }),
    "desde=2027-01-04&hasta=2027-01-10",
  );
});

test("fecha sola se mantiene para la vista diaria", () => {
  assert.equal(construirQueryTurnos({ fecha: "2027-01-04" }), "fecha=2027-01-04");
});

test("sin filtros devuelve cadena vacía", () => {
  assert.equal(construirQueryTurnos({}), "");
});

test("rango más profesional conserva el orden de parámetros", () => {
  const query = construirQueryTurnos({
    desde: "2027-01-04",
    hasta: "2027-01-10",
    profesional_id: "44444444-4444-4444-4444-444444444444",
  });

  assert.equal(
    query,
    "desde=2027-01-04&hasta=2027-01-10&profesional_id=44444444-4444-4444-4444-444444444444",
  );
});

test("codifica los valores que lo necesitan", () => {
  assert.equal(construirQueryTurnos({ sillon_id: "a&b c" }), "sillon_id=a%26b+c");
});

test("rutaTurnos arma la ruta del endpoint con y sin filtros", () => {
  assert.equal(
    rutaTurnos({ desde: "2027-01-04", hasta: "2027-01-10" }),
    "/api/v1/turnos?desde=2027-01-04&hasta=2027-01-10",
  );
  assert.equal(rutaTurnos({ fecha: "2027-01-04" }), "/api/v1/turnos?fecha=2027-01-04");
  assert.equal(rutaTurnos({}), "/api/v1/turnos");
});
