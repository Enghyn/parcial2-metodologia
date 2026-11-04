import assert from "node:assert/strict";
import { test } from "node:test";

import { construirUrlWhatsapp } from "../src/shared/utils/whatsapp.ts";

test("normaliza el teléfono y codifica el mensaje", () => {
  const url = construirUrlWhatsapp("+54 9 11 4455-6677", "Hola, turno 10:00");
  assert.equal(url, "https://wa.me/5491144556677?text=Hola%2C%20turno%2010%3A00");
});

test("sin teléfono devuelve cadena vacía", () => {
  assert.equal(construirUrlWhatsapp("", "Hola"), "");
  assert.equal(construirUrlWhatsapp("---", "Hola"), "");
});
