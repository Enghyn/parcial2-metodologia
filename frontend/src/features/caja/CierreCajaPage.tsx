// Pantalla de cierre diario de caja (C-12).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  cerrarCaja,
  cuentaCorriente,
  exportCajaCsv,
  listarCierres,
  listarMovimientos,
  resumenDiario,
} from "../../shared/api/caja";
import type { Cierre, Movimiento } from "../../shared/api/caja";
import { formatFecha, formatHora, toIsoDate } from "../../shared/date";
import { formatArs } from "../../shared/utils/format";

const FORM_INICIAL = { fecha_dia: "" as string };

export function CierreCajaPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.rol === "admin";
  const [fecha, setFecha] = useState<string>(toIsoDate(new Date()));
  const [cierres, setCierres] = useState<Cierre[]>([]);
  const [movimientos, setMovimientos] = useState<Movimiento[]>([]);
  const [resumen, setResumen] = ReturnType<typeof import("../../shared/api/caja")>["ResumenDiario"] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [guardando, setGuardando] = useState<boolean>(false);
  const [exportando, setExportando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  useEffect(() => {
    let activo = true;
    setLoading(true);
    setError(null);
    listarCierres()
      .then((cs) => {
        if (activo) setCierres(cs);
      })
      .catch(() => {
        if (activo) setError("No pudimos cargar los cierres.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, []);

  useEffect(() => {
    if (!fecha) return;
    let activo = true;
    setLoading(true);
    Promise.all([listarMovimientos(fecha), resumenDiario(fecha)]).then(
      ([movs, res]) => {
        if (!activo) return;
        setMovimientos(movs);
        setResumen(res);
      }
    );
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    .finally(() => {
      if (activo) setLoading(false);
    });
    return () => {
      activo = false;
    };
  }, [fecha]);

  async function handleCerrar(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    setMensaje(null);
    setGuardando(true);
    try {
      await cerrarCaja({ fecha_dia: fecha === "" ? undefined : fecha });
      setMensaje("Día cerrado correctamente.");
      const actualizados = await listarCierres();
      setCierres(actualizados);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cerrar el día.");
    } finally {
      setGuardando(false);
    }
  }

  async function handleExportar(): Promise<void> {
    setExportando(true);
    try {
      const csv = await exportCajaCsv(fecha === "" ? undefined : fecha);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `caja-${fecha === "" ? toIsoDate(new Date()) : fecha}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo exportar el CSV.");
    } finally {
      setExportando(false);
    }
  }

  if (!isAdmin) {
    return (
      <section className="p-4">
        <h1 className="text-xl font-semibold">Cierre de caja</h1>
        <p className="text-sm text-rose-600">Solo el administrador puede cerrar la caja del día.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Cierre diario de caja</h1>
          <p className="text-sm text-foreground/70">
            El cierre aprueba el balance del día y bloquea nuevos movimientos para esa fecha.
          </p>
        </div>
      </header>

      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      {mensaje !== null && <p className="text-sm text-green-600">{mensaje}</p>}
      {loading && <p className="text-sm text-foreground/60">Cargando cierres...</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Total ingresos", resumen?.total_ingresos ?? "0"],
          ["Total egresos", resumen?.total_egresos ?? "0"],
          ["Balance", resumen?.balance ?? "0"],
        ].map(([label, monto]) => (
          <div key={String(label)} className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">{label}</p>
            <p className="text-lg font-semibold">{formatArs(Number(monto))}</p>
          </div>
        ))}
      </div>

      <form onSubmit={(event) => void handleCerrar(event)} className="rounded border border-border p-4">
        <h2 className="text-sm font-semibold">Cerrar día</h2>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <label className="text-sm">
            Fecha
            <input
              type="date"
              value={fecha}
              onChange={(event) => setFecha(event.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
            />
          </label>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={guardando}
              className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
            >
              {guardando ? "Cerrando..." : "Cerrar día"}
            </button>
          </div>
        </div>
        <p className="text-xs text-foreground/50 mt-1">
          Solo el administrador puede cerrar el día. Una vez cerrado, no se pueden registrar nuevos
          movimientos para esa fecha.
        </p>
      </form>

      <div className="rounded border border-border p-4">
        <h2 className="text-sm font-semibold">Movimientos del día</h2>
        <div className="overflow-x-auto">
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
              {movimientos.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-foreground/60">
                    No hay movimientos para esta fecha.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="mt-2 flex justify-end">
          <button
            onClick={handleExportar}
            disabled={exportando}
            className="rounded border border-border px-4 py-2 text-sm disabled:opacity-60"
          >
            {exportando ? "Exportando..." : "Exportar CSV del día"}
          </button>
        </div>
      </div>

      <div className="rounded border border-border p-4">
        <h2 className="text-sm font-semibold">Historial de cierres</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/40">
              <tr>
                <th className="px-3 py-2">Fecha</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 text-right">Balance</th>
                <th className="px-3 py-2">Aprobado por</th>
                <th className="px-3 py-2">Aprobado en</th>
              </tr>
            </thead>
            <tbody>
              {cierres.map((cierre) => (
                <tr key={cierre.id} className="border-t border-border">
                  <td className="px-3 py-2">{formatFecha(cierre.fecha_dia)}</td>
                  <td className="px-3 py-2">{cierre.estado}</td>
                  <td className="px-3 py-2 text-right">{formatArs(Number(cierre.balance))}</td>
                  <td className="px-3 py-2">{cierre.aprobado_por ?? "—"}</td>
                  <td className="px-3 py-2">{cierre.aprobado_en ?? "—"}</td>
                </tr>
              ))}
              {cierres.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-foreground/60">
                    No hay cierres registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
