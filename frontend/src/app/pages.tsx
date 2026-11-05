import type { ReactElement } from "react";
import { formatArs } from "../shared/utils/format";
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

export function PresupuestoPublicoPage(): ReactElement {
  const totalEjemplo = 120000;
  return (
    <section>
      <h1>Tu presupuesto</h1>
      <p>Revisá el detalle y aprobalo con un clic. Total estimado: {formatArs(totalEjemplo)}.</p>
    </section>
  );
}

export function PagarPage(): ReactElement {
  return (
    <section>
      <h1>Pagá tu seña</h1>
      <p>Completá el pago online de forma segura. Te mostramos el monto en pesos argentinos.</p>
    </section>
  );
}