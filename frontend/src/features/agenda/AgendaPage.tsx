// Vista principal de la agenda interna.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../app/AuthContext";
import { useAgendaStore } from "./useAgendaStore";
import { DateSelector } from "./DateSelector";
import { AgendaColumn } from "./AgendaColumn";
import { TurnoModal } from "./TurnoModal";
import { ReprogramarModal } from "./ReprogramarModal";
import { VistaToggle } from "./VistaToggle";
import { toIsoDate } from "./dateUtils";
import type { EstadoTurno } from "../../shared/api/agenda";
import type { TurnoOut } from "../../shared/api/agenda";

export function AgendaPage(): ReactElement {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const {
    fechaSeleccionada,
    turnos,
    sillones,
    profesionales,
    pacientes,
    loading,
    error,
    cargar,
    crear,
    crearSobreturno,
    reprogramar,
    cambiarEstado,
  } = useAgendaStore();

  const [modalOpen, setModalOpen] = useState(false);
  const [reprogramando, setReprogramando] = useState<TurnoOut | null>(null);

  useEffect(() => {
    const hoy = toIsoDate(new Date());
    void cargar(hoy);
  }, [cargar]);

  const rol = user?.rol ?? "";
  const canCreate = rol === "admin" || rol === "recepcion";

  const pacienteNombre = (id: string): string =>
    pacientes.find((p) => p.id === id)?.nombre ?? id;
  const profesionalNombre = (id: string): string =>
    profesionales.find((p) => p.id === id)?.nombre ?? id;

  function handleCambiarEstado(id: string, estado: EstadoTurno): void {
    void cambiarEstado(id, estado);
  }

  function handleFechaChange(fecha: string): void {
    void cargar(fecha);
  }

  async function handleCrear(input: Parameters<typeof crear>[0]): Promise<void> {
    await crear(input);
  }

  async function handleCrearSobreturno(
    input: Parameters<typeof crear>[0],
    motivo: string,
  ): Promise<void> {
    await crearSobreturno(input, motivo);
  }

  function handleLogout(): void {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <section className="p-4">
      <header className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold">Agenda del día</h1>
          {user !== null && (
            <p className="text-sm text-foreground/70">
              {user.nombre} · {user.rol}
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="w-full sm:w-auto">
            <VistaToggle />
          </div>
          {canCreate && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex min-h-11 flex-1 items-center justify-center whitespace-nowrap rounded bg-primary px-4 py-2 text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:flex-none"
            >
              Nuevo turno
            </button>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex min-h-11 flex-1 items-center justify-center whitespace-nowrap rounded border border-border px-4 py-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:flex-none"
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="mb-4">
        <DateSelector
          fecha={fechaSeleccionada === "" ? toIsoDate(new Date()) : fechaSeleccionada}
          onChange={handleFechaChange}
        />
      </div>

      {error !== null && <p className="mb-2 text-sm text-rose-600">{error}</p>}
      {loading && <p className="mb-2 text-sm text-foreground/60">Cargando...</p>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {sillones.map((sillon) => (
          <AgendaColumn
            key={sillon.id}
            sillon={sillon}
            turnos={turnos.filter((t) => t.sillon_id === sillon.id)}
            pacienteNombre={pacienteNombre}
            profesionalNombre={profesionalNombre}
            rol={rol}
            onCambiarEstado={handleCambiarEstado}
            onReprogramar={setReprogramando}
          />
        ))}
      </div>

      <TurnoModal
        open={modalOpen}
        catalogos={{ sillones, profesionales, pacientes }}
        onClose={() => setModalOpen(false)}
        onCrear={handleCrear}
        onCrearSobreturno={handleCrearSobreturno}
      />
      <ReprogramarModal
        turno={reprogramando}
        onClose={() => setReprogramando(null)}
        onReprogramar={reprogramar}
      />
    </section>
  );
}