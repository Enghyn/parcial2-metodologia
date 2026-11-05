import assert from "node:assert/strict";
import { test } from "node:test";

import { mensajeRateLimit, parseRetryAfter } from "../src/shared/rateLimit.ts";

test("parseRetryAfter", () => {
  assert.equal(parseRetryAfter("12"), 12);
  assert.equal(parseRetryAfter(null), null);
  assert.equal(parseRetryAfter("no-numero"), null);
});

test("mensajeRateLimit", () => {
  assert.match(mensajeRateLimit(12), /12 segundos/);
});