import type { ReactElement } from "react";
import { formatArs } from "../shared/utils/format";

export function LoginPage(): ReactElement {
  return (
    <section>
      <h1>Ingresá a tu cuenta</h1>
      <p>Si sos parte del equipo del consultorio, iniciá sesión para ver la agenda.</p>
    </section>
  );
}

export function AppHomePage(): ReactElement {
  return (
    <section>
      <h1>Agenda del día</h1>
      <p>Acá vas a ver los turnos de hoy por sillón.</p>
    </section>
  );
}

export function ReservarPage(): ReactElement {
  const senaEjemplo = 5000;
  return (
    <section>
      <h1>Reservá tu turno</h1>
      <p>Elegí el día y la hora que te quede cómoda. Te lo confirmamos por WhatsApp.</p>
      <p>Seña para reservar: {formatArs(senaEjemplo)}. La seña no es reembolsable si cancelás fuera de término.</p>
    </section>
  );
}

export function TurnoPublicoPage(): ReactElement {
  return (
    <section>
      <h1>Tu turno</h1>
      <p>Acá podés confirmar, cancelar o reprogramar tu turno sin llamar al consultorio.</p>
    </section>
  );
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
