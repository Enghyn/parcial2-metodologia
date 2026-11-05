// Conmutador Diaria / Semanal (D8). `NavLink` marca la opción activa con
// `aria-current="page"` y, además, se anuncia “(vista activa)” a lectores.
import type { ReactElement } from "react";
import { NavLink } from "react-router-dom";

const BASE = "inline-flex min-h-11 items-center px-3 text-sm";
const ACTIVO = `${BASE} bg-primary/10 font-semibold text-primary`;
const INACTIVO = `${BASE} text-foreground/70 hover:bg-foreground/5`;

export function VistaToggle(): ReactElement {
  return (
    <div
      className="inline-flex overflow-hidden rounded border border-border"
      role="group"
      aria-label="Vista de agenda"
    >
      <NavLink to="/app/agenda" end className={({ isActive }) => (isActive ? ACTIVO : INACTIVO)}>
        {({ isActive }) => (
          <>
            Diaria
            {isActive && <span className="sr-only"> (vista activa)</span>}
          </>
        )}
      </NavLink>
      <NavLink
        to="/app/agenda/semana"
        className={({ isActive }) => (isActive ? ACTIVO : INACTIVO)}
      >
        {({ isActive }) => (
          <>
            Semanal
            {isActive && <span className="sr-only"> (vista activa)</span>}
          </>
        )}
      </NavLink>
    </div>
  );
}
