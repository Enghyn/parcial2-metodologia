// Pantalla de facturación por medio de pago y obra social (C-21).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  descargarCsv,
  exportarFacturacionCsv,
  reporteFacturacion,
  type FacturacionMedio,
  type FacturacionOS,
  type FacturacionReporte,
} from "../../shared/api/reportes";
import { addDays, toIsoDate, hoy } from "../../shared/date";
import { formatArs } from "../../shared/utils/format";

const ROL_CAJA = (rol: string | undefined) => rol === "admin" || rol === "recepcion";

export function FacturacionPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canAccess = ROL_CAJA(user?.rol);
  const hoyISO = toIsoDate(hoy());
  const defaultDesde = toIsoDate(addDays(hoy(), -30));
  const [desde, setDesde] = useState<string>(defaultDesde);
  const [hasta, setHasta] = useState<string>(hoyISO);
  const [reporte, setReporte] = useState<FacturacionReporte | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportando, setExportando] = useState<boolean>(false);

  useEffect(() => {
    if (!canAccess) return;
    let activo = true;
    setLoading(true);
    setError(null);
    reporteFacturacion(desde || undefined, hasta || undefined)
      .then((data) => {
        if (activo) setReporte(data);
      })
      .catch((err) => {
        if (activo)
          setError(err instanceof Error ? err.message : "No se pudo cargar el reporte.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [canAccess, desde, hasta]);

  async function handleExportar(): Promise<void> {
    if (!canAccess) return;
    setExportando(true);
    setError(null);
    try {
      const contenido = await exportarFacturacionCsv(desde || undefined, hasta || undefined);
      descargarCsv(
        contenido,
        `facturacion-${desde.replace(/-/g, "")}_${hasta.replace(/-/g, "")}.csv`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo exportar el CSV.");
    } finally {
      setExportando(false);
    }
  }

  if (!canAccess) {
    return (
      <section className="p-4">
        <h1 className="text-xl font-semibold">Facturación</h1>
        <p className="text-sm text-rose-600">
          Acceso restringido a administración y recepción.
        </p>
      </section>
    );
  }

  const porMedio = reporte?.por_medio_pago ?? [];
  const porOS = reporte?.por_obra_social ?? [];
  const totalIngresos = Number(reporte?.total_ingresos ?? "0");
  const balance = Number(reporte?.balance_neto ?? "0");

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Facturación por medio de pago y obra social</h1>
          <p className="text-sm text-foreground/70">
            Ingresos del libro de caja agrupados por medio y desglose de obra social.
          </p>
        </div>
        <button
          onClick={handleExportar}
          disabled={exportando || loading || reporte === null}
          className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
        >
          {exportando ? "Exportando..." : "Exportar CSV"}
        </button>
      </header>

      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      {loading && reporte === null && <p className="text-sm text-foreground/60">Cargando...</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-sm">
          Desde
          <input
            type="date"
            value={desde}
            onChange={(event) => setDesde(event.target.value)}
            className="ml-2 rounded border border-border px-3 py-2"
          />
        </label>
        <label className="text-sm">
          Hasta
          <input
            type="date"
            value={hasta}
            onChange={(event) => setHasta(event.target.value)}
            className="ml-2 rounded border border-border px-3 py-2"
          />
        </label>
      </div>

      {reporte === null ? null : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">Ingresos</p>
              <p className="text-lg font-semibold">{formatArs(totalIngresos)}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">Balance neto</p>
              <p className="text-lg font-semibold">{formatArs(balance)}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">
                Medios con actividad
              </p>
              <p className="text-lg font-semibold">{porMedio.length}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">
                Obras sociales con actividad
              </p>
              <p className="text-lg font-semibold">{porOS.length}</p>
            </div>
          </div>

          <h2 className="text-sm font-semibold mt-6">Por medio de pago</h2>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2">Medio de pago</th>
                  <th className="px-3 py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {porMedio.map((m: FacturacionMedio) => (
                  <tr key={m.medio_pago} className="border-t border-border">
                    <td className="px-3 py-2">{m.medio_pago}</td>
                    <td className="px-3 py-2 text-right">{formatArs(Number(m.total))}</td>
                  </tr>
                ))}
                {porMedio.length === 0 && (
                  <tr>
                    <td colSpan={2} className="px-3 py-4 text-center text-foreground/60">
                      Sin ingresos en el rango seleccionado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <h2 className="text-sm font-semibold mt-6">Por obra social</h2>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2">Obra social</th>
                  <th className="px-3 py-2 text-right">Monto OS</th>
                  <th className="px-3 py-2 text-right">Copago paciente</th>
                  <th className="px-3 py-2 text-right">Total paciente</th>
                </tr>
              </thead>
              <tbody>
                {porOS.map((o: FacturacionOS) => (
                  <tr key={o.obra_social} className="border-t border-border">
                    <td className="px-3 py-2">{o.obra_social}</td>
                    <td className="px-3 py-2 text-right">{formatArs(Number(o.monto_os))}</td>
                    <td className="px-3 py-2 text-right">{formatArs(Number(o.copago_paciente))}</td>
                    <td className="px-3 py-2 text-right">{formatArs(Number(o.total_paciente))}</td>
                  </tr>
                ))}
                {porOS.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-center text-foreground/60">
                      Sin desglose de obra social en el rango seleccionado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
