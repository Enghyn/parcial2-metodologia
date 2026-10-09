import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  login: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  accessToken: null,
  login: (token: string): void => {
    set({ accessToken: token });
  },
  logout: (): void => {
    set({ accessToken: null });
  },
}));
