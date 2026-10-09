import type { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout, PublicLayout, RequireAuth } from "./layout";
import {
  AppHomePage,
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
            <Route path="agenda" element={<AppHomePage />} />
          </Route>
        </Route>
        <Route element={<PublicLayout />}>
          <Route path="/reservar/:slug" element={<ReservarPage />} />
          <Route path="/p/turno/:token" element={<TurnoPublicoPage />} />
          <Route path="/p/presupuesto/:token" element={<PresupuestoPublicoPage />} />
          <Route path="/p/pagar/:token" element={<PagarPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
