// Vista principal de la agenda interna.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../app/AuthContext";
import { useAgendaStore } from "./useAgendaStore";
import { DateSelector } from "./DateSelector";
import { AgendaColumn } from "./AgendaColumn";
import { TurnoModal } from "./TurnoModal";
import { toIsoDate } from "./dateUtils";
import type { EstadoTurno } from "../../shared/api/agenda";

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
    cambiarEstado,
  } = useAgendaStore();

  const [modalOpen, setModalOpen] = useState(false);

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

  function handleLogout(): void {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <section className="p-4">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Agenda del día</h1>
          {user !== null && (
            <p className="text-sm text-foreground/70">
              {user.nombre} · {user.rol}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {canCreate && (
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="rounded bg-primary px-4 py-2 text-primary-foreground"
            >
              Nuevo turno
            </button>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="rounded border border-border px-4 py-2"
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
          />
        ))}
      </div>

      <TurnoModal
        open={modalOpen}
        catalogos={{ sillones, profesionales, pacientes }}
        onClose={() => setModalOpen(false)}
        onCrear={handleCrear}
      />
    </section>
  );
}