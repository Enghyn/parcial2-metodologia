import type { ReactElement } from "react";
import { Navigate, Outlet } from "react-router-dom";
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
