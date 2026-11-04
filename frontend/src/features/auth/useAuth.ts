// Hook de auth para componentes (login/logout/me).
import { useAuthStore } from "../../app/AuthContext";
import { me as meApi } from "../../shared/api/auth";
import type { UsuarioPerfil } from "../../shared/api/auth";

export interface UseAuthResult {
  user: UsuarioPerfil | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
}

export function useAuth(): UseAuthResult {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const refreshMe = async (): Promise<void> => {
    const perfil = await meApi();
    useAuthStore.setState({ user: perfil });
  };
  return { user, accessToken, login, logout, refreshMe };
}