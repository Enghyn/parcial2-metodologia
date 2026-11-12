// Resumen público del presupuesto (C-18, task 5.1): ítems, total en ARS y estado.
// Los montos y el estado legible salen de `presentacion.ts` (R10, testeado puro).
import type { ReactElement } from "react";
import type { PresupuestoPublico } from "../../shared/api/public";
import { totalEnArs, vistaPresupuesto } from "./presentacion";

interface ResumenPresupuestoProps {
  presupuesto: PresupuestoPublico;
}

export function ResumenPresupuesto({ presupuesto }: ResumenPresupuestoProps): ReactElement {
  const vista = vistaPresupuesto(presupuesto);

  return (
    <section className="space-y-3 rounded border border-border p-4">
      <h2 className="text-lg font-medium">Detalle del presupuesto</h2>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-foreground/60">
            <th className="py-1">Prestación</th>
            <th className="py-1 text-right">Cant.</th>
            <th className="py-1 text-right">Arancel</th>
            <th className="py-1 text-right">Copago</th>
          </tr>
        </thead>
        <tbody>
          {presupuesto.items.map((item, indice) => (
            <tr key={`${item.descripcion}-${indice}`} className="border-t border-border">
              <td className="py-1">{item.descripcion}</td>
              <td className="py-1 text-right">{item.cantidad}</td>
              <td className="py-1 text-right">{totalEnArs(item.arancel)}</td>
              <td className="py-1 text-right">{totalEnArs(item.copago)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-right text-base font-semibold">Total: {vista.totalTexto}</p>
      <p className="text-sm uppercase tracking-wide text-foreground/70">
        Estado: {vista.estadoTexto}
      </p>
    </section>
  );
}
