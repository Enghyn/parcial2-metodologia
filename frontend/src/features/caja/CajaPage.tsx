// Pantalla de caja (C-08): libro diario, cobros/egresos y balance.
import type { FormEvent, ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import { listarTurnos } from "../../shared/api/agenda";
import type { TurnoOut } from "../../shared/api/agenda";
import {
  crearMovimiento,
  listarMovimientos,
  resumenDiario,
} from "../../shared/api/caja";
import type { MedioPago, Movimiento, ResumenDiario, TipoMovimiento } from "../../shared/api/caja";
import { formatFecha, formatHora, toIsoDate } from "../../shared/date";
import { formatArs } from "../../shared/utils/format";

const MEDIOS: { value: MedioPago; label: string }[] = [
  { value: "efectivo", label: "Efectivo" },
  { value: "transferencia", label: "Transferencia" },
  { value: "debito", label: "Débito" },
  { value: "credito", label: "Crédito" },
  { value: "otro", label: "Otro" },
];

const FORM_INICIAL = {
  tipo: "ingreso" as TipoMovimiento,
  medio_pago: "efectivo" as MedioPago,
  monto: "",
  concepto: "",
  turno_id: "",
};

export function CajaPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canAccess = user?.rol === "admin" || user?.rol === "recepcion";
  const [fecha, setFecha] = useState<string>(toIsoDate(new Date()));
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [resumen, setResumen] = useState<ResumenDiario | null>(null);
  const [turnos, setTurnos] = useState<TurnoOut[]>([]);
  const [form, setForm] = useState(FORM_INICIAL);
  const [recarga, setRecarga] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [guardando, setGuardando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const turnoSel = turnos.find((t) => t.id === form.turno_id);
  const senaPendiente =
    turnoSel !== undefined &&
    Number(turnoSel.sena_monto) > 0 &&
    !movimientos.some(
      (m) =>
        m.turno_id === turnoSel.id &&
        m.tipo === "ingreso" &&
        m.concepto.toLowerCase().includes("seña"),
    );

  useEffect(() => {
    if (!canAccess) return;
    let activo = true;
    setLoading(true);
    setError(null);
    Promise.all([listarMovimientos(fecha), resumenDiario(fecha), listarTurnos({ fecha })])
      .then(([movs, res, ts]) => {
        if (!activo) return;
        setMovimientos(movs);
        setResumen(res);
        setTurnos(ts);
      })
      .catch(() => {
        if (activo) setError("No pudimos cargar la caja.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [fecha, recarga, canAccess]);

  function actualizar(campo: keyof typeof FORM_INICIAL, valor: string): void {
    setForm((actual) => ({ ...actual, [campo]: valor }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    if (form.concepto.trim() === "" || Number(form.monto) <= 0) {
      setError("Ingresá un monto mayor a cero y un concepto.");
      return;
    }
    setGuardando(true);
    try {
      await crearMovimiento({
        tipo: form.tipo,
        medio_pago: form.medio_pago,
        monto: form.monto,
        concepto: form.concepto.trim(),
        turno_id: form.turno_id === "" ? null : form.turno_id,
      });
      setForm({ ...FORM_INICIAL, tipo: form.tipo, medio_pago: form.medio_pago });
      setRecarga((n) => n + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos registrar el movimiento.");
    } finally {
      setGuardando(false);
    }
  }

  if (!canAccess) {
    return (
      <section className="p-4">
        <h1 className="text-xl font-semibold">Caja</h1>
        <p className="text-sm text-rose-600">Acceso restringido a administración y recepción.</p>
      </section>
    );
  }

  const efectivo = Number(resumen?.por_medio_pago.efectivo ?? "0");
  const transferencia = Number(resumen?.por_medio_pago.transferencia ?? "0");
  const tarjetas =
    Number(resumen?.por_medio_pago.debito ?? "0") +
    Number(resumen?.por_medio_pago.credito ?? "0");
  const total = Number(resumen?.total_ingresos ?? "0");
  const egresos = Number(resumen?.total_egresos ?? "0");
  const balance = Number(resumen?.balance ?? "0");

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Caja del día</h1>
          <p className="text-sm text-foreground/70">Libro append-only: las correcciones son contra-asientos.</p>
        </div>
        <label className="text-sm">
          Fecha
          <input
            type="date"
            value={fecha}
            onChange={(event) => setFecha(event.target.value)}
            className="ml-2 rounded border border-border px-3 py-2"
          />
        </label>
      </header>

      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      {loading && <p className="text-sm text-foreground/60">Cargando caja...</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ["Efectivo", efectivo],
          ["Transferencias", transferencia],
          ["Tarjetas", tarjetas],
          ["Total del día", total],
          ["Egresos", egresos],
          ["Balance", balance],
        ].map(([label, monto]) => (
          <div key={String(label)} className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">{label}</p>
            <p className="text-lg font-semibold">{formatArs(Number(monto))}</p>
          </div>
        ))}
      </div>

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-2 rounded border border-border p-4">
        <h2 className="text-sm font-semibold">Nuevo movimiento</h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-sm">
            Tipo
            <select
              value={form.tipo}
              onChange={(event) => actualizar("tipo", event.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
            >
              <option value="ingreso">Ingreso</option>
              <option value="egreso">Egreso</option>
            </select>
          </label>
          <label className="text-sm">
            Medio
            <select
              value={form.medio_pago}
              onChange={(event) => actualizar("medio_pago", event.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
            >
              {MEDIOS.map((medio) => (
                <option key={medio.value} value={medio.value}>
                  {medio.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Monto (ARS)
            <input
              value={form.monto}
              onChange={(event) => actualizar("monto", event.target.value)}
              inputMode="decimal"
              className="mt-1 w-full rounded border border-border px-3 py-2"
              placeholder="15000.00"
            />
          </label>
          <label className="text-sm">
            Concepto
            <input
              value={form.concepto}
              onChange={(event) => actualizar("concepto", event.target.value)}
              maxLength={255}
              className="mt-1 w-full rounded border border-border px-3 py-2"
              placeholder="Cobro de consulta"
            />
          </label>
        </div>
        <label className="block text-sm">
          Turno (opcional)
          <select
            value={form.turno_id}
            onChange={(event) => actualizar("turno_id", event.target.value)}
            className="mt-1 w-full rounded border border-border px-3 py-2"
          >
            <option value="">Sin turno</option>
            {turnos.map((turno) => (
              <option key={turno.id} value={turno.id}>
                {turno.prestacion} · {formatHora(turno.inicio)} · {turno.estado}
              </option>
            ))}
          </select>
        </label>
        {senaPendiente && (
          <p className="text-sm text-amber-700">
            Este turno tiene una seña de {formatArs(Number(turnoSel?.sena_monto ?? 0))}. Si ya se
            cobró, registrala como ingreso con concepto “Seña de reserva”.
          </p>
        )}
        <button
          type="submit"
          disabled={guardando}
          className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
        >
          {guardando ? "Guardando..." : "Registrar movimiento"}
        </button>
      </form>

      <div className="overflow-x-auto rounded border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Medio</th>
              <th className="px-3 py-2">Concepto</th>
              <th className="px-3 py-2 text-right">Monto</th>
            </tr>
          </thead>
          <tbody>
            {movimientos.map((movimiento) => (
              <tr key={movimiento.id} className="border-t border-border">
                <td className="px-3 py-2">
                  {formatFecha(movimiento.fecha)} {formatHora(movimiento.fecha)}
                </td>
                <td className="px-3 py-2">{movimiento.tipo}</td>
                <td className="px-3 py-2">{movimiento.medio_pago}</td>
                <td className="px-3 py-2">{movimiento.concepto}</td>
                <td className="px-3 py-2 text-right">{formatArs(Number(movimiento.monto))}</td>
              </tr>
            ))}
            {movimientos.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-foreground/60">
                  No hay movimientos para esta fecha.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
