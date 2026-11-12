// Marca única del consultorio para todas las superficies públicas (C-18, task 5.4).
// R2: sin slug, tenant ni selector de sucursal; la marca es fija.
import type { ReactElement } from "react";
import { marcaConsultorio } from "./presentacion";

export function MarcaConsultorio(): ReactElement {
  const marca = marcaConsultorio();

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-3xl items-center px-6 py-3">
        <span className="text-lg font-semibold">{marca.nombre}</span>
      </div>
    </header>
  );
}
