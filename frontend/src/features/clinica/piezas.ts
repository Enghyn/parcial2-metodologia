// Piezas FDI del odontograma: 32 piezas permanentes en 4 cuadrantes.
export interface CuadranteFDI {
  titulo: string;
  piezas: number[];
}

export const CUADRANTES_FDI: CuadranteFDI[] = [
  { titulo: "Cuadrante 1 · superior derecho", piezas: [18, 17, 16, 15, 14, 13, 12, 11] },
  { titulo: "Cuadrante 2 · superior izquierdo", piezas: [21, 22, 23, 24, 25, 26, 27, 28] },
  { titulo: "Cuadrante 3 · inferior izquierdo", piezas: [31, 32, 33, 34, 35, 36, 37, 38] },
  { titulo: "Cuadrante 4 · inferior derecho", piezas: [48, 47, 46, 45, 44, 43, 42, 41] },
];

export const PIEZAS_FDI: number[] = CUADRANTES_FDI.flatMap((cuadrante) => cuadrante.piezas);
