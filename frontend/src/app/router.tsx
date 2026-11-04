import type { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout, PublicLayout, RequireAuth } from "./layout";
import { AgendaPage } from "../features/agenda/AgendaPage";
import { OdontogramaPage, PacientesPage } from "../features/clinica";
import {
  LoginPage,
  PagarPage,
  PresupuestoPublicoPage,
  ReservarPage,
  TurnoPublicoPage,
} from "./pages";

export function AppRouter(): ReactElement {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Navigate to="/app/agenda" replace />} />
            <Route path="agenda" element={<AgendaPage />} />
            <Route path="pacientes" element={<PacientesPage />} />
            <Route path="odontograma/:pacienteId" element={<OdontogramaPage />} />
          </Route>
        </Route>
        <Route element={<PublicLayout />}>
          <Route path="/reservar" element={<ReservarPage />} />
          <Route path="/p/turno/:token" element={<TurnoPublicoPage />} />
          <Route path="/p/presupuesto/:token" element={<PresupuestoPublicoPage />} />
          <Route path="/p/pagar/:token" element={<PagarPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
