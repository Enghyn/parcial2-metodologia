import assert from "node:assert/strict";
import { test } from "node:test";

import { formatHora } from "../src/shared/date.ts";

test("formatHora usa 24 horas en la zona del consultorio", () => {
  // 13:00Z = 10:00 ART
  assert.equal(formatHora("2026-11-12T13:00:00Z"), "10:00");
  // 01:30Z del día siguiente = 22:30 ART (el caso que mostraba "10:30 p. m.")
  assert.equal(formatHora("2026-11-05T01:30:00Z"), "22:30");
});

test("formatHora no usa sufijos a. m. / p. m.", () => {
  const tarde = formatHora("2026-11-05T01:30:00Z");
  const manana = formatHora("2026-11-12T13:00:00Z");

  assert.equal(/[ap]\.\s?m\./.test(tarde), false);
  assert.equal(/[ap]\.\s?m\./.test(manana), false);
});

test("formatHora muestra la medianoche como 00:00 y no 24:00", () => {
  // 03:00Z = 00:00 ART
  assert.equal(formatHora("2026-11-05T03:00:00Z"), "00:00");
});
