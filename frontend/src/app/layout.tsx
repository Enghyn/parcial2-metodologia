import type { ReactElement } from "react";
import { Navigate, NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "./AuthContext";

export function RequireAuth(): ReactElement {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (accessToken === null) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export function AppLayout(): ReactElement {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <nav className="flex gap-4 p-3 text-sm">
          <NavLink
            to="/app/agenda"
            className={({ isActive }) => (isActive ? "font-semibold underline" : "underline")}
          >
            Agenda
          </NavLink>
          <NavLink
            to="/app/pacientes"
            className={({ isActive }) => (isActive ? "font-semibold underline" : "underline")}
          >
            Pacientes
          </NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export function PublicLayout(): ReactElement {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main>
        <Outlet />
      </main>
    </div>
  );
}
