import { create } from "zustand";

interface TenantState {
  slug: string | null;
  nombre: string | null;
  setTenant: (slug: string, nombre: string) => void;
  clearTenant: () => void;
}

export const useTenantStore = create<TenantState>()((set) => ({
  slug: null,
  nombre: null,
  setTenant: (slug: string, nombre: string): void => {
    set({ slug, nombre });
  },
  clearTenant: (): void => {
    set({ slug: null, nombre: null });
  },
}));
