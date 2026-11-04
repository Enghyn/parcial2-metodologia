// Formulario de login (D7).
import type { ReactElement, FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";

export function LoginForm(): ReactElement {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(email, password);
      navigate("/app/agenda", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Credenciales inválidas");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="mx-auto max-w-sm space-y-4 p-6">
      <h1 className="text-xl font-semibold">Ingresá a tu cuenta</h1>
      <p className="text-sm text-foreground/70">
        Si sos parte del equipo del consultorio, iniciá sesión para ver la agenda.
      </p>
      <div className="space-y-1">
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full rounded border border-border px-3 py-2"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="password" className="block text-sm font-medium">
          Contraseña
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full rounded border border-border px-3 py-2"
        />
      </div>
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
      >
        {pending ? "Ingresando..." : "Ingresar"}
      </button>
    </form>
  );
}