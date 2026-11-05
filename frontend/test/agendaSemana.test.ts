import assert from "node:assert/strict";
import { test } from "node:test";

import type { TurnoOut } from "../src/shared/api/agenda.ts";
import type { Sillon } from "../src/features/agenda/types.ts";
import {
  agruparSemana,
  claveCelda,
  construirCeldas,
  diasSemana,
  filtrarPorProfesional,
  filaSemana,
  formatearRangoSemana,
  inicioSemana,
  rangoSemana,
  turnosDeSemana,
} from "../src/features/agenda/semanaUtils.ts";

const SILLONES: Sillon[] = [
  { id: "s1", nombre: "Sillón 1", activo: true },
  { id: "s2", nombre: "Sillón 2", activo: true },
  { id: "s3", nombre: "Sillón 3", activo: true },
];

function turno(parcial: Partial<TurnoOut> & Pick<TurnoOut, "id" | "inicio" | "sillon_id">): TurnoOut {
  return {
    paciente_id: "p1",
    profesional_id: "prof1",
    prestacion: "Consulta",
    fin: parcial.inicio,
    duracion_min: 30,
    estado: "reservado",
    token_publico: "t",
    sena_monto: "0.00",
    notas: null,
    es_sobreturno: false,
    motivo_sobreturno: null,
    autorizado_por: null,
    created_at: parcial.inicio,
    updated_at: parcial.inicio,
    ...parcial,
  };
}

// --- Semana lunes–domingo en ART (D5) -------------------------------------

test("el lunes de un miércoles es el lunes anterior", () => {
  assert.equal(inicioSemana("2026-11-04"), "2026-11-02");
});

test("un domingo pertenece a la semana que empieza el lunes anterior", () => {
  assert.equal(inicioSemana("2026-11-08"), "2026-11-02");
});

test("el lunes se devuelve a sí mismo", () => {
  assert.equal(inicioSemana("2026-11-02"), "2026-11-02");
});

test("la semana que cruza el año se resuelve sin huecos", () => {
  assert.equal(inicioSemana("2027-01-01"), "2026-12-28");

  const dias = diasSemana("2026-12-28");
  assert.equal(dias.length, 7);
  assert.deepEqual(
    dias.map((dia) => dia.iso),
    [
      "2026-12-28",
      "2026-12-29",
      "2026-12-30",
      "2026-12-31",
      "2027-01-01",
      "2027-01-02",
      "2027-01-03",
    ],
  );
});

test("diasSemana devuelve siete días consecutivos con etiquetas es-AR", () => {
  const dias = diasSemana("2026-11-02");

  assert.deepEqual(dias[0], { iso: "2026-11-02", nombre: "lun", dia: 2, mes: "nov" });
  assert.deepEqual(dias[6], { iso: "2026-11-08", nombre: "dom", dia: 8, mes: "nov" });
  assert.equal(new Set(dias.map((dia) => dia.iso)).size, 7);
});

test("rangoSemana devuelve desde/hasta inclusivos", () => {
  assert.deepEqual(rangoSemana("2027-01-04"), { desde: "2027-01-04", hasta: "2027-01-10" });
});

test("formatearRangoSemana arma el título en español rioplatense", () => {
  assert.equal(formatearRangoSemana("2026-11-02"), "lunes 2 – domingo 8 de noviembre de 2026");
});

test("formatearRangoSemana nombra los dos meses cuando la semana los cruza", () => {
  assert.equal(
    formatearRangoSemana("2026-12-28"),
    "lunes 28 de diciembre – domingo 3 de enero de 2027",
  );
});

test("filaSemana agrupa los turnos por día en orden cronológico", () => {
  const turnos = [
    turno({ id: "b", inicio: "2026-11-04T12:00:00Z", sillon_id: "s1" }),
    turno({ id: "a", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" }),
  ];

  const filas = filaSemana(turnos, "2026-11-02", SILLONES[0]);

  assert.equal(filas.length, 7);
  assert.deepEqual(filas[0].map((t) => t.id), ["a"]);
  assert.deepEqual(filas[2].map((t) => t.id), ["b"]);
  assert.deepEqual(filas[1], []);
});

// --- Agrupación y celdas ---------------------------------------------------

test("agruparSemana indexa por sillón y fecha", () => {
  const turnos = [
    turno({ id: "a", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" }),
    turno({ id: "b", inicio: "2026-11-03T12:00:00Z", sillon_id: "s2" }),
  ];

  const grupos = agruparSemana(turnos, "2026-11-02");

  assert.deepEqual(grupos[claveCelda("s1", "2026-11-02")].map((t) => t.id), ["a"]);
  assert.deepEqual(grupos[claveCelda("s2", "2026-11-03")].map((t) => t.id), ["b"]);
  assert.equal(grupos[claveCelda("s1", "2026-11-03")], undefined);
});

test("construirCeldas arma 7 × 3 celdas, sillón por fila y día por columna", () => {
  const celdas = construirCeldas([], "2026-11-02", SILLONES);

  assert.equal(celdas.length, 21);
  assert.deepEqual(
    celdas.slice(0, 2).map((celda) => [celda.sillonId, celda.fecha]),
    [
      ["s1", "2026-11-02"],
      ["s1", "2026-11-03"],
    ],
  );
  assert.deepEqual(
    celdas.slice(19, 21).map((celda) => [celda.sillonId, celda.fecha]),
    [
      ["s3", "2026-11-07"],
      ["s3", "2026-11-08"],
    ],
  );
});

test("construirCeldas ignora los sillones inactivos", () => {
  const sillones: Sillon[] = [
    { id: "s1", nombre: "Sillón 1", activo: true },
    { id: "s2", nombre: "Sillón 2", activo: false },
  ];

  const celdas = construirCeldas([], "2026-11-02", sillones);

  assert.equal(celdas.length, 7);
  assert.ok(celdas.every((celda) => celda.sillonId === "s1"));
});

test("cada celda lista sus turnos ordenados por hora de inicio", () => {
  const turnos = [
    turno({ id: "tarde", inicio: "2026-11-02T18:00:00Z", sillon_id: "s1" }),
    turno({ id: "manana", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" }),
    turno({ id: "otro", inicio: "2026-11-03T12:00:00Z", sillon_id: "s1" }),
  ];

  const celdas = construirCeldas(turnos, "2026-11-02", SILLONES);
  const lunes = celdas.find((celda) => celda.sillonId === "s1" && celda.fecha === "2026-11-02");

  assert.deepEqual(lunes?.turnos.map((t) => t.id), ["manana", "tarde"]);
  assert.deepEqual(
    celdas.find((celda) => celda.sillonId === "s1" && celda.fecha === "2026-11-03")?.turnos.map(
      (t) => t.id,
    ),
    ["otro"],
  );
});

test("las celdas sin turnos quedan vacías y conservan el flag de sobreturno", () => {
  const turnos = [
    turno({
      id: "sob",
      inicio: "2026-11-05T13:15:00Z",
      sillon_id: "s2",
      es_sobreturno: true,
      estado: "confirmado",
    }),
  ];

  const celdas = construirCeldas(turnos, "2026-11-02", SILLONES);
  const conTurno = celdas.find(
    (celda) => celda.sillonId === "s2" && celda.fecha === "2026-11-05",
  );
  const vacias = celdas.filter((celda) => celda.turnos.length === 0);

  assert.equal(conTurno?.turnos[0].es_sobreturno, true);
  assert.equal(vacias.length, 20);
});

// --- Filtro por profesional (D7) ------------------------------------------

test("filtrarPorProfesional con null devuelve todos los turnos", () => {
  const turnos = [
    turno({ id: "a", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" }),
    turno({
      id: "b",
      inicio: "2026-11-02T13:00:00Z",
      sillon_id: "s1",
      profesional_id: "prof2",
    }),
  ];

  assert.equal(filtrarPorProfesional(turnos, null).length, 2);
});

test("filtrarPorProfesional deja solo los turnos del profesional", () => {
  const turnos = [
    turno({ id: "a", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" }),
    turno({
      id: "b",
      inicio: "2026-11-02T13:00:00Z",
      sillon_id: "s1",
      profesional_id: "prof2",
    }),
  ];

  assert.deepEqual(
    filtrarPorProfesional(turnos, "prof2").map((t) => t.id),
    ["b"],
  );
});

test("filtrarPorProfesional sin coincidencias devuelve lista vacía", () => {
  const turnos = [turno({ id: "a", inicio: "2026-11-02T12:00:00Z", sillon_id: "s1" })];

  assert.deepEqual(filtrarPorProfesional(turnos, "prof-inexistente"), []);
});

// --- 6.5 TRIANGULATE: límites de zona horaria y estabilidad ----------------

test("un instante del domingo 23:00 ART cae en la semana anterior", () => {
  // 2027-01-04T02:00:00Z = domingo 2027-01-03 23:00 ART.
  assert.equal(inicioSemana("2027-01-04T02:00:00Z"), "2026-12-28");
});

test("un turno del domingo 23:30 ART aparece en la columna del domingo", () => {
  // 2027-01-11T02:30:00Z = domingo 2027-01-10 23:30 ART.
  const turnos = [
    turno({ id: "domingo-noche", inicio: "2027-01-11T02:30:00Z", sillon_id: "s1" }),
  ];

  const celdas = construirCeldas(turnos, "2027-01-04", SILLONES);
  const domingo = celdas.find((celda) => celda.sillonId === "s1" && celda.fecha === "2027-01-10");
  const lunesSiguiente = celdas.filter((celda) => celda.fecha === "2027-01-11");

  assert.deepEqual(domingo?.turnos.map((t) => t.id), ["domingo-noche"]);
  assert.deepEqual(lunesSiguiente, []);
});

test("una semana sin turnos deja las 21 celdas vacías", () => {
  const celdas = construirCeldas([], "2026-11-09", SILLONES);

  assert.equal(celdas.length, 21);
  assert.ok(celdas.every((celda) => celda.turnos.length === 0));
});

test("dos turnos con el mismo inicio mantienen un orden estable", () => {
  const mismoInicio = "2026-11-05T13:00:00Z";
  const turnos = [
    turno({ id: "zeta", inicio: mismoInicio, sillon_id: "s1" }),
    turno({ id: "alfa", inicio: mismoInicio, sillon_id: "s1", es_sobreturno: true }),
  ];

  const primera = construirCeldas(turnos, "2026-11-02", SILLONES);
  const segunda = construirCeldas([...turnos].reverse(), "2026-11-02", SILLONES);
  const celda = (celdas: typeof primera) =>
    celdas.find((c) => c.sillonId === "s1" && c.fecha === "2026-11-05")?.turnos.map((t) => t.id);

  assert.deepEqual(celda(primera), ["alfa", "zeta"]);
  assert.deepEqual(celda(segunda), ["alfa", "zeta"]);
});

test("turnosDeSemana descarta los que quedaron fuera del rango mostrado", () => {
  const turnos = [
    turno({ id: "en-semana", inicio: "2026-11-05T13:00:00Z", sillon_id: "s1" }),
    turno({ id: "fuera", inicio: "2026-11-12T13:00:00Z", sillon_id: "s1" }),
  ];

  assert.deepEqual(
    turnosDeSemana(turnos, "2026-11-02").map((t) => t.id),
    ["en-semana"],
  );
});

