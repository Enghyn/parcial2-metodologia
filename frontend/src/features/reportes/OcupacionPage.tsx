// Pantalla de ocupación por sillón y profesional (C-21).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  descargarCsv,
  exportarOcupacionCsv,
  reporteOcupacion,
  type OcupacionRecurso,
  type OcupacionReporte,
} from "../../shared/api/reportes";
import { addDays, toIsoDate, hoy } from "../../shared/date";

const ROL_PUEDE_LEER = (rol: string | undefined) =>
  rol === "admin" || rol === "recepcion" || rol === "odontologo";

export function OcupacionPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canAccess = ROL_PUEDE_LEER(user?.rol);
  const hoyISO = toIsoDate(hoy());
  const defaultDesde = toIsoDate(addDays(hoy(), -30));
  const [desde, setDesde] = useState<string>(defaultDesde);
  const [hasta, setHasta] = useState<string>(hoyISO);
  const [profesionalId, setProfesionalId] = useState<string>("");
  const [sillonId, setSillonId] = useState<string>("");
  const [reporte, setReporte] = useState<OcupacionReporte | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exportando, setExportando] = useState<boolean>(false);

  useEffect(() => {
    if (!canAccess) return;
    let activo = true;
    setLoading(true);
    setError(null);
    reporteOcupacion(
      desde || undefined,
      hasta || undefined,
      profesionalId || undefined,
      sillonId || undefined,
    )
      .then((data) => {
        if (activo) setReporte(data);
      })
      .catch((err) => {
        if (activo) setError(err instanceof Error ? err.message : "No se pudo cargar el reporte.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [canAccess, desde, hasta, profesionalId, sillonId]);

  async function handleExportar(): Promise<void> {
    if (!canAccess) return;
    setExportando(true);
    setError(null);
    try {
      const contenido = await exportarOcupacionCsv(
        desde || undefined,
        hasta || undefined,
        profesionalId || undefined,
        sillonId || undefined,
      );
      descargarCsv(
        contenido,
        `ocupacion-${desde.replace(/-/g, "")}_${hasta.replace(/-/g, "")}.csv`,
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
        <h1 className="text-xl font-semibold">Ocupación</h1>
        <p className="text-sm text-rose-600">
          Acceso restringido a administración, recepción y odontología.
        </p>
      </section>
    );
  }

  const sillones = reporte?.sillones ?? [];
  const profesionales = reporte?.profesionales ?? [];
  const totalAtendido = sillones.reduce((a, s) => a + s.atendido, 0) + profesionales.reduce(
    (a, p) => a + p.atendido,
    0,
  );

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Ocupación por sillón y profesional</h1>
          <p className="text-sm text-foreground/70">
            Turnos atendidos vs reservados, tasa de ocupación y horas bloqueadas.
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
        <label className="text-sm">
          Profesional (ID)
          <input
            value={profesionalId}
            onChange={(event) => setProfesionalId(event.target.value)}
            className="ml-2 rounded border border-border px-3 py-2"
            placeholder="UUID del profesional"
          />
        </label>
        <label className="text-sm">
          Sillón (ID)
          <input
            value={sillonId}
            onChange={(event) => setSillonId(event.target.value)}
            className="ml-2 rounded border border-border px-3 py-2"
            placeholder="UUID del sillón"
          />
        </label>
      </div>

      {reporte === null ? null : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">Atendidos</p>
              <p className="text-lg font-semibold">{totalAtendido}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">
                Sillones con actividad
              </p>
              <p className="text-lg font-semibold">{sillones.length}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">
                Profesionales con actividad
              </p>
              <p className="text-lg font-semibold">{profesionales.length}</p>
            </div>
            <div className="rounded border border-border bg-background p-3">
              <p className="text-xs uppercase tracking-wide text-foreground/60">
                Turnos del período
              </p>
              <p className="text-lg font-semibold">
                {sillones.reduce((a, s) => a + s.reservado + s.confirmado + s.presente + s.atendido + s.cancelado, 0)}
              </p>
            </div>
          </div>

          <h2 className="text-sm font-semibold mt-6">Por sillón</h2>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2">Sillón</th>
                  <th className="px-3 py-2 text-center">Reservado</th>
                  <th className="px-3 py-2 text-center">Confirmado</th>
                  <th className="px-3 py-2 text-center">Presente</th>
                  <th className="px-3 py-2 text-center">Atendido</th>
                  <th className="px-3 py-2 text-center">Cancelado</th>
                  <th className="px-3 py-2 text-right">Tasa</th>
                  <th className="px-3 py-2 text-right">Hrs. bloqueadas</th>
                </tr>
              </thead>
              <tbody>
                {sillones.map((s: OcupacionRecurso) => (
                  <tr key={s.id} className="border-t border-border">
                    <td className="px-3 py-2">{s.nombre}</td>
                    <td className="px-3 py-2 text-center">{s.reservado}</td>
                    <td className="px-3 py-2 text-center">{s.confirmado}</td>
                    <td className="px-3 py-2 text-center">{s.presente}</td>
                    <td className="px-3 py-2 text-center">{s.atendido}</td>
                    <td className="px-3 py-2 text-center">{s.cancelado}</td>
                    <td className="px-3 py-2 text-right">
                      {(s.tasa_ocupacion * 100).toFixed(0)}%
                    </td>
                    <td className="px-3 py-2 text-right">{s.horas_bloqueadas.toFixed(2)} h</td>
                  </tr>
                ))}
                {sillones.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-3 py-4 text-center text-foreground/60">
                      Sin turnos en el rango seleccionado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <h2 className="text-sm font-semibold mt-6">Por profesional</h2>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2">Profesional</th>
                  <th className="px-3 py-2 text-center">Reservado</th>
                  <th className="px-3 py-2 text-center">Confirmado</th>
                  <th className="px-3 py-2 text-center">Presente</th>
                  <th className="px-3 py-2 text-center">Atendido</th>
                  <th className="px-3 py-2 text-center">Cancelado</th>
                  <th className="px-3 py-2 text-right">Tasa</th>
                  <th className="px-3 py-2 text-right">Hrs. bloqueadas</th>
                </tr>
              </thead>
              <tbody>
                {profesionales.map((p: OcupacionRecurso) => (
                  <tr key={p.id} className="border-t border-border">
                    <td className="px-3 py-2">{p.nombre}</td>
                    <td className="px-3 py-2 text-center">{p.reservado}</td>
                    <td className="px-3 py-2 text-center">{p.confirmado}</td>
                    <td className="px-3 py-2 text-center">{p.presente}</td>
                    <td className="px-3 py-2 text-center">{p.atendido}</td>
                    <td className="px-3 py-2 text-center">{p.cancelado}</td>
                    <td className="px-3 py-2 text-right">
                      {(p.tasa_ocupacion * 100).toFixed(0)}%
                    </td>
                    <td className="px-3 py-2 text-right">{p.horas_bloqueadas.toFixed(2)} h</td>
                  </tr>
                ))}
                {profesionales.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-3 py-4 text-center text-foreground/60">
                      Sin turnos en el rango seleccionado.
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
