// Tests puros del portal público (C-18, tasks 4.1 y 5.1–5.4).
// El runner es `node --test` con type-stripping: NO procesa JSX, así que la
// lógica de presentación de las páginas vive en `presentacion.ts` (sin JSX) y
// los componentes `.tsx` solo la conectan a la vista. Mismo patrón que
// `features/reserva-publica/retencion.ts` y `features/agenda/semanaUtils.ts`.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  construirAprobacion,
  construirRechazo,
  rutaAprobarPresupuestoPublico,
  rutaConfirmarPagoPublico,
  rutaPagoPublico,
  rutaPresupuestoPublico,
  rutaRechazarPresupuestoPublico,
} from "../src/shared/api/public.ts";
import {
  MENSAJE_NO_ENCONTRADO,
  esErrorConflicto,
  esErrorNoEncontrado,
  estadoPagoLegible,
  estadoPresupuestoLegible,
  marcaConsultorio,
  puedeConfirmarPago,
  puedeEnviarFirma,
  resultadoPago,
  totalEnArs,
  vistaPresupuesto,
} from "../src/features/portal-publico/presentacion.ts";

// Normaliza el espacio duro (NBSP, U+00A0) que usa Intl para separar el símbolo.
const sinNbsp = (texto: string): string => texto.replace(/\u00a0/g, " ");

// --- 4.1 Cliente de API del portal (frontend) ------------------------------

test("4.1 los constructores de URL llevan el token en el path", () => {
  assert.equal(rutaPresupuestoPublico("tok-1"), "/api/v1/public/presupuestos/tok-1");
  assert.equal(
    rutaAprobarPresupuestoPublico("tok-1"),
    "/api/v1/public/presupuestos/tok-1/aprobar",
  );
  assert.equal(
    rutaRechazarPresupuestoPublico("tok-1"),
    "/api/v1/public/presupuestos/tok-1/rechazar",
  );
  assert.equal(rutaPagoPublico("tok-1"), "/api/v1/public/pagos/tok-1");
  assert.equal(rutaConfirmarPagoPublico("tok-1"), "/api/v1/public/pagos/tok-1/confirmar");
});

test("4.1 el token opaco no viaja en query string (R9)", () => {
  const rutas = [
    rutaPresupuestoPublico("tok-secreto"),
    rutaAprobarPresupuestoPublico("tok-secreto"),
    rutaPagoPublico("tok-secreto"),
    rutaConfirmarPagoPublico("tok-secreto"),
  ];
  assert.ok(rutas.every((ruta) => !ruta.includes("?")));
  assert.ok(rutas.every((ruta) => ruta.startsWith("/api/v1/public/")));
});

test("4.1 construirAprobacion recorta la firma antes de enviarla", () => {
  assert.deepEqual(construirAprobacion("  Ana Pérez  "), { firma: "Ana Pérez" });
});

test("4.1 construirRechazo omite el motivo vacío y recorta el válido", () => {
  assert.deepEqual(construirRechazo(), {});
  assert.deepEqual(construirRechazo("   "), {});
  assert.deepEqual(construirRechazo(null), {});
  assert.deepEqual(construirRechazo("  Muy caro  "), { motivo: "Muy caro" });
});

test("4.1 las funciones tipadas del portal están exportadas", async () => {
  const api = await import("../src/shared/api/public.ts");
  assert.equal(typeof api.getPresupuestoPublico, "function");
  assert.equal(typeof api.aprobarPresupuestoPublico, "function");
  assert.equal(typeof api.rechazarPresupuestoPublico, "function");
  assert.equal(typeof api.getPagoPublico, "function");
  assert.equal(typeof api.confirmarPagoPublico, "function");
});

// --- 5.1 ResumenPresupuesto / FirmaSimple ----------------------------------

test("5.1 el total se formatea en pesos argentinos (R10)", () => {
  assert.equal(sinNbsp(totalEnArs(120000)), "$ 120.000,00");
  assert.equal(sinNbsp(totalEnArs(1500.5)), "$ 1.500,50");
});

test("5.1 una firma vacía o en blanco no permite enviar", () => {
  assert.equal(puedeEnviarFirma(""), false);
  assert.equal(puedeEnviarFirma("    "), false);
  assert.equal(puedeEnviarFirma("Ana"), true);
});

test("5.1 vistaPresupuesto refleja estado, total y acciones disponibles", () => {
  const vista = vistaPresupuesto({
    estado: "enviado",
    total: 120000,
    items: [{ descripcion: "Consulta", cantidad: 1, arancel: 120000, copago: 0 }],
  });

  assert.equal(vista.estadoTexto, "Enviado");
  assert.equal(vista.puedeAprobar, true);
  assert.equal(vista.puedeRechazar, true);
  assert.equal(sinNbsp(vista.totalTexto), "$ 120.000,00");
});

// --- 5.2 PresupuestoPublicoPage --------------------------------------------

test("5.2 tras aprobar, el estado visible es Aprobado y no se puede volver a firmar", () => {
  const vista = vistaPresupuesto({ estado: "aprobado", total: 90000, items: [] });

  assert.equal(vista.estadoTexto, "Aprobado");
  assert.equal(vista.puedeAprobar, false);
  assert.equal(vista.puedeRechazar, false);
});

test("5.2 tras rechazar, el estado visible es Rechazado", () => {
  const vista = vistaPresupuesto({ estado: "rechazado", total: 90000, items: [] });

  assert.equal(vista.estadoTexto, "Rechazado");
  assert.equal(vista.puedeAprobar, false);
});

test("5.2 un token inválido se reconoce como 404 genérico", () => {
  assert.equal(esErrorNoEncontrado({ status: 404 }), true);
  assert.equal(esErrorNoEncontrado({ status: 409 }), false);
  assert.equal(esErrorNoEncontrado(new Error("boom")), false);
  assert.equal(MENSAJE_NO_ENCONTRADO.includes("No encontramos"), true);
});

test("5.2 un presupuesto no firmable se reconoce como conflicto", () => {
  assert.equal(esErrorConflicto({ status: 409 }), true);
  assert.equal(esErrorConflicto({ status: 404 }), false);
});

// --- 5.3 PagarPage / ResultadoPago -----------------------------------------

test("5.3 un pago pendiente habilita confirmar solo si no hay request en curso", () => {
  const pago = { estado: "pendiente", monto: 50000, confirmado_en: null };

  assert.equal(puedeConfirmarPago(pago, false), true);
  // Con la request en curso el botón queda deshabilitado: el doble clic no dispara dos confirmaciones.
  assert.equal(puedeConfirmarPago(pago, true), false);
});

test("5.3 un pago ya aprobado no vuelve a habilitar el botón (idempotencia)", () => {
  const pago = { estado: "aprobado", monto: 50000, confirmado_en: "2026-11-12T10:00:00Z" };

  assert.equal(puedeConfirmarPago(pago, false), false);
});

test("5.3 resultadoPago distingue aprobado de rechazado e informa el monto en ARS", () => {
  const aprobado = resultadoPago({
    estado: "aprobado",
    monto: 120000,
    confirmado_en: "2026-11-12T10:00:00Z",
  });
  assert.equal(aprobado.aprobado, true);
  assert.equal(aprobado.rechazado, false);
  assert.equal(aprobado.texto.includes("120.000"), true);

  const rechazado = resultadoPago({ estado: "rechazado", monto: 120000, confirmado_en: null });
  assert.equal(rechazado.aprobado, false);
  assert.equal(rechazado.rechazado, true);
  assert.equal(estadoPagoLegible("rechazado"), "Rechazado");
});

// --- 5.4 MarcaConsultorio --------------------------------------------------

test("5.4 la marca del consultorio es única y no expone slug ni tenant (R2)", () => {
  const marca = marcaConsultorio();

  assert.equal(typeof marca.nombre, "string");
  assert.equal(marca.nombre.length > 0, true);
  assert.equal("slug" in marca, false);
  assert.equal("tenant" in marca, false);
  assert.equal("sucursal" in marca, false);
});

test("5.4 los estados legibles están en español rioplatense", () => {
  assert.equal(estadoPresupuestoLegible("enviado"), "Enviado");
  assert.equal(estadoPresupuestoLegible("aprobado"), "Aprobado");
  assert.equal(estadoPagoLegible("pendiente"), "Pendiente");
});
