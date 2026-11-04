// Store de autenticación (Zustand) extendido: token + perfil + persistencia (D2, D7).
import { create } from "zustand";
import { login as loginApi, me as meApi } from "../shared/api/auth";
import type { UsuarioPerfil } from "../shared/api/auth";

interface AuthState {
  accessToken: string | null;
  user: UsuarioPerfil | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hydrate: () => void;
}

const STORAGE_KEY = "odonto.accessToken";

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  user: null,
  login: async (email: string, password: string): Promise<void> => {
    const tokenOut = await loginApi({ email, password });
    set({ accessToken: tokenOut.access_token });
    window.localStorage.setItem(STORAGE_KEY, tokenOut.access_token);
    try {
      const perfil = await meApi();
      set({ user: perfil });
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
      set({ accessToken: null, user: null });
      throw new Error("No se pudo obtener el perfil");
    }
  },
  logout: (): void => {
    window.localStorage.removeItem(STORAGE_KEY);
    set({ accessToken: null, user: null });
  },
  hydrate: (): void => {
    const token = window.localStorage.getItem(STORAGE_KEY);
    if (token === null) return;
    set({ accessToken: token });
    void meApi()
      .then((perfil) => set({ user: perfil }))
      .catch(() => {
        window.localStorage.removeItem(STORAGE_KEY);
        set({ accessToken: null, user: null });
      });
  },
}));