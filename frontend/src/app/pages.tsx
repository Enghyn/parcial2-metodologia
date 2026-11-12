import type { ReactElement } from "react";
import { AgendaPage } from "../features/agenda/AgendaPage";
import { LoginForm } from "../features/auth/LoginForm";
import {
  ReprogramarPublicoPage as ReprogramarPublicoDetalle,
  ReservarWizard,
  TurnoPublicoPage as TurnoPublicoDetalle,
} from "../features/reserva-publica";

export function LoginPage(): ReactElement {
  return <LoginForm />;
}

export function AppHomePage(): ReactElement {
  return <AgendaPage />;
}

export function ReservarPage(): ReactElement {
  return <ReservarWizard />;
}

export function TurnoPublicoPage(): ReactElement {
  return <TurnoPublicoDetalle />;
}

export function ReprogramarPublicoPage(): ReactElement {
  return <ReprogramarPublicoDetalle />;
}