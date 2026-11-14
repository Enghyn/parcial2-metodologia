// Pantalla de ausentismo y recuperación (C-21).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  descargarCsv,
  exportarAusentismoCsv,
  reporteAusentismo,
  type AusentismoReporte,
} from "../../shared/api/reportes";
import { addDays, toIsoDate, hoy } from "../../shared/date";

const ROL_CAJA = (rol: string | undefined) => rol === "admin" || rol === "recepcion";

export function AusentismoPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canAccess = ROL_CAJA(user?.rol);
  const hoyISO = toIsoDate(hoy());
  const defaultDesde = toIsoDate(addDays(hoy(), -30));
  const [desde, setDesde] = useState<string>(defaultDesde);
  const [hasta, setHasta] = useState<string>(hoyISO);
  const [reporte, setReporte] = useState<AusentismoReporte | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportando, setExportando] = useState<boolean>(false);

  useEffect(() => {
    if (!canAccess) return;
    let activo = true;
    setLoading(true);
    setError(null);
    reporteAusentismo(desde || undefined, hasta || undefined)
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
      const contenido = await exportarAusentismoCsv(desde || undefined, hasta || undefined);
      descargarCsv(
        contenido,
        `ausentismo-${desde.replace(/-/g, "")}_${hasta.replace(/-/g, "")}.csv`,
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
        <h1 className="text-xl font-semibold">Ausentismo</h1>
        <p className="text-sm text-rose-600">
          Acceso restringido a administración y recepción.
        </p>
      </section>
    );
  }

  const cancelados = reporte?.cancelados ?? 0;
  const noPresentados = reporte?.no_presentados ?? 0;
  const recuperados = reporte?.recuperados ?? 0;
  const totalTurnos = reporte?.total_turnos ?? 0;
  const tasa = reporte?.tasa_ausentismo ?? 0;

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Ausentismo y recuperación</h1>
          <p className="text-sm text-foreground/70">
            Turnos cancelados / no presentados, reagendados y tasa de ausentismo.
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
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">Cancelados</p>
            <p className="text-lg font-semibold">{cancelados}</p>
          </div>
          <div className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">No presentados</p>
            <p className="text-lg font-semibold">{noPresentados}</p>
          </div>
          <div className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">Recuperados</p>
            <p className="text-lg font-semibold">{recuperados}</p>
          </div>
          <div className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">Tasa de ausentismo</p>
            <p className="text-lg font-semibold">{ (tasa * 100).toFixed(1) }%</p>
          </div>
          <div className="rounded border border-border bg-background p-3">
            <p className="text-xs uppercase tracking-wide text-foreground/60">Turnos del período</p>
            <p className="text-lg font-semibold">{totalTurnos}</p>
          </div>
        </div>
      )}
    </section>
  );
}
