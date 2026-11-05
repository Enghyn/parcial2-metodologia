// Vista semanal interna (C-09b, US-001): 7 días × N sillones en una sola consulta.
import type { ReactElement } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../app/AuthContext";
import type { EstadoTurno, ReprogramarInput, TurnoOut } from "../../shared/api/agenda";
import { toIsoDate } from "../../shared/date";
import { estadoClasses } from "./estadoColor";
import { FiltroProfesional } from "./FiltroProfesional";
import { ReprogramarModal } from "./ReprogramarModal";
import { SemanaGrid } from "./SemanaGrid";
import { SelectorSemana } from "./SelectorSemana";
import { VistaToggle } from "./VistaToggle";
import { useAgendaStore } from "./useAgendaStore";
import {
  filtrarPorProfesional,
  formatearRangoSemana,
  inicioSemana,
  rangoSemana,
  sumarDias,
  turnosDeSemana,
} from "./semanaUtils";
import type { EstadoTurno as EstadoTurnoAlias } from "./types";

const ESTADOS: EstadoTurno[] = [
  "reservado",
  "confirmado",
  "presente",
  "atendido",
  "cancelado",
  "ausente",
];

function contar(cantidad: number, singular: string, plural: string): string {
  return `${cantidad} ${cantidad === 1 ? singular : plural}`;
}

function SemanaSkeleton({ filas }: { filas: number }): ReactElement {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="overflow-x-auto rounded border border-border"
    >
      <span className="sr-only">Cargando la semana…</span>
      <div className="min-w-[940px] p-2">
        {Array.from({ length: filas + 1 }, (_, fila) => (
          <div key={fila} className="mb-1 grid grid-cols-[82px_repeat(7,1fr)] gap-1">
            {Array.from({ length: 8 }, (_, columna) => (
              <span
                key={columna}
                className={`h-14 rounded bg-foreground/5 ${
                  columna === 0 ? "" : "animate-pulse motion-reduce:animate-none"
                }`}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SemanaPage(): ReactElement {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const {
    turnos,
    sillones,
    profesionales,
    pacientes,
    loading,
    error,
    errorCarga,
    semana,
    cargarSemana,
    cambiarEstado,
    reprogramar,
  } = useAgendaStore();

  const [lunes, setLunes] = useState<string>(() => inicioSemana(new Date()));
  const [profesionalId, setProfesionalId] = useState<string | null>(null);
  const [seleccionado, setSeleccionado] = useState<TurnoOut | null>(null);
  const [reprogramando, setReprogramando] = useState<TurnoOut | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const cargaIniciada = useRef<string | null>(null);

  const { desde, hasta } = rangoSemana(lunes);
  const hoyIso = toIsoDate(new Date());
  const enSemanaActual = lunes === inicioSemana(new Date());

  useEffect(() => {
    // Una sola consulta por rango: el doble efecto de StrictMode no repite la request.
    const clave = `${desde}|${hasta}`;
    if (cargaIniciada.current === clave) return;
    cargaIniciada.current = clave;
    void cargarSemana(desde, hasta);
  }, [cargarSemana, desde, hasta]);

  const visibles = useMemo(
    () => turnosDeSemana(filtrarPorProfesional(turnos, profesionalId), lunes),
    [turnos, profesionalId, lunes],
  );

  const pacienteNombre = useCallback(
    (id: string): string => pacientes.find((p) => p.id === id)?.nombre ?? "Paciente",
    [pacientes],
  );
  const profesionalNombre = useCallback(
    (id: string): string => profesionales.find((p) => p.id === id)?.nombre ?? "Profesional",
    [profesionales],
  );

  function irA(nuevoLunes: string): void {
    setSeleccionado(null);
    setAviso(null);
    setLunes(nuevoLunes);
  }

  function handleSeleccionar(turno: TurnoOut): void {
    setSeleccionado((actual) => (actual !== null && actual.id === turno.id ? null : turno));
  }

  function handleCambiarEstado(id: string, estado: EstadoTurnoAlias): void {
    void cambiarEstado(id, estado);
  }

  function handleReprogramar(turno: TurnoOut): void {
    setSeleccionado(null);
    setReprogramando(turno);
  }

  async function confirmarReprogramacion(id: string, datos: ReprogramarInput): Promise<void> {
    await reprogramar(id, datos);
    const semanaDestino = inicioSemana(datos.inicio);
    if (semanaDestino !== lunes) {
      setAviso(
        `El turno quedó agendado fuera de esta semana: ${formatearRangoSemana(semanaDestino)}.`,
      );
    } else {
      setAviso(null);
    }
  }

  function handleLogout(): void {
    logout();
    navigate("/login", { replace: true });
  }

  const rol = user?.rol ?? "";
  const resumen = `${contar(visibles.length, "turno", "turnos")} · ${contar(
    sillones.filter((sillon) => sillon.activo).length,
    "sillón activo",
    "sillones activos",
  )} · ${contar(profesionales.length, "profesional", "profesionales")}`;
  // El vacío de semana solo aplica sin filtro: con un profesional sin turnos la
  // grilla sigue visible con las celdas libres (spec `internal-agenda`).
  const cargandoSemana = errorCarga === null && (loading || semana?.desde !== desde);
  const semanaVacia = errorCarga === null && !cargandoSemana && turnos.length === 0;
  const errorAccion = errorCarga === null && error !== null && reprogramando === null;

  return (
    <section className="mx-auto max-w-[1200px] p-4">
      <header className="mb-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-foreground/60">
              Agenda interna · vista semanal
            </p>
            <h1 className="text-xl font-semibold">{formatearRangoSemana(lunes)}</h1>
            <p className="text-sm text-foreground/70">
              {resumen}
              {user !== null && <span className="ml-2 text-foreground/50">· {user.nombre}</span>}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="min-h-11 rounded border border-border px-4 text-sm hover:bg-foreground/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="mb-4 flex flex-wrap items-center gap-3 rounded border border-border p-2">
        <SelectorSemana
          onAnterior={() => irA(sumarDias(lunes, -7))}
          onHoy={() => irA(inicioSemana(new Date()))}
          onSiguiente={() => irA(sumarDias(lunes, 7))}
          enSemanaActual={enSemanaActual}
        />
        <div className="hidden flex-1 sm:block" />
        <VistaToggle />
        <FiltroProfesional
          profesionales={profesionales}
          valor={profesionalId}
          onChange={setProfesionalId}
        />
      </div>

      <div
        className="mb-3 flex flex-wrap items-center gap-3 text-[11px]"
        aria-label="Referencias de estado"
      >
        <span className="font-semibold uppercase tracking-wide text-foreground/60">Estados</span>
        {ESTADOS.map((estado) => (
          <span key={estado} className="inline-flex items-center gap-1">
            <span
              aria-hidden="true"
              className={`h-2.5 w-2.5 rounded-full border ${estadoClasses(estado)}`}
            />
            <span className="capitalize">{estado}</span>
          </span>
        ))}
        <span className="inline-flex items-center rounded border border-dashed border-foreground/40 px-1 text-[10px] font-bold uppercase tracking-wide">
          Sobreturno
        </span>
      </div>

      {aviso !== null && (
        <p role="status" className="mb-3 rounded border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900">
          {aviso}
        </p>
      )}

      {errorCarga !== null && (
        <div role="alert" className="rounded border border-rose-300 bg-rose-50 p-4 text-sm text-rose-900">
          <p className="font-semibold">No pudimos cargar la semana.</p>
          <p className="mt-1">
            Revisá la conexión y volvé a intentar. Si el problema sigue, avisale al administrador.
          </p>
          <button
            type="button"
            onClick={() => void cargarSemana(desde, hasta)}
            className="mt-3 min-h-11 rounded border border-rose-400 px-4 hover:bg-rose-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          >
            Reintentar
          </button>
        </div>
      )}

      {errorAccion && (
        <p role="alert" className="mb-3 rounded border border-rose-300 bg-rose-50 p-2 text-sm text-rose-900">
          {error}
        </p>
      )}

      {cargandoSemana && <SemanaSkeleton filas={Math.max(sillones.length, 3)} />}

      {semanaVacia && (
        <div role="status" className="rounded border border-dashed border-border p-8 text-center">
          <p className="text-2xl text-foreground/30" aria-hidden="true">
            —
          </p>
          <h2 className="mt-2 text-base font-semibold">No hay turnos en esta semana</h2>
          <p className="mt-1 text-sm text-foreground/70">
            {formatearRangoSemana(lunes)} no tiene turnos cargados para los filtros actuales.
          </p>
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            <NavLink
              to="/app/agenda"
              className="inline-flex min-h-11 items-center rounded bg-primary px-4 text-sm text-primary-foreground"
            >
              Ir a la vista diaria
            </NavLink>
            <button
              type="button"
              onClick={() => irA(sumarDias(lunes, 7))}
              className="min-h-11 rounded border border-border px-4 text-sm hover:bg-foreground/5"
            >
              Ver la semana siguiente
            </button>
          </div>
        </div>
      )}

      {errorCarga === null && !cargandoSemana && !semanaVacia && (
        <SemanaGrid
          lunes={lunes}
          sillones={sillones}
          turnos={visibles}
          hoyIso={hoyIso}
          rol={rol}
          seleccionadoId={seleccionado?.id ?? null}
          pacienteNombre={pacienteNombre}
          profesionalNombre={profesionalNombre}
          onSeleccionar={handleSeleccionar}
          onCambiarEstado={handleCambiarEstado}
          onReprogramar={handleReprogramar}
        />
      )}

      <p className="mt-2 text-[11px] text-foreground/60">
        Elegí un turno para cambiar su estado o reprogramarlo. Las celdas “Libre” marcan huecos
        disponibles y no crean turnos al hacer clic.
      </p>

      <ReprogramarModal
        turno={reprogramando}
        onClose={() => setReprogramando(null)}
        onReprogramar={confirmarReprogramacion}
      />
    </section>
  );
}
