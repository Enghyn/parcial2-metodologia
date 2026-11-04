// CatalogosProvider + cargarCatalogos con fallback estático del seed (D3).
import type { ReactElement, ReactNode } from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { request, ApiError } from "../../shared/api/client";
import type { Sillon, Profesional, Paciente, Catalogos } from "./types";

const FALLBACK_SILLONES: Sillon[] = [
  { id: "11111111-1111-1111-1111-111111111111", nombre: "Sillón 1", activo: true },
  { id: "22222222-2222-2222-2222-222222222222", nombre: "Sillón 2", activo: true },
  { id: "33333333-3333-3333-3333-333333333333", nombre: "Sillón 3", activo: true },
];

const FALLBACK_PROFESIONALES: Profesional[] = [
  { id: "44444444-4444-4444-4444-444444444444", nombre: "Dr. Pérez" },
  { id: "55555555-5555-5555-5555-555555555555", nombre: "Dra. Gómez" },
];

const FALLBACK_PACIENTES: Paciente[] = [
  { id: "66666666-6666-6666-6666-666666666666", nombre: "María López" },
  { id: "77777777-7777-7777-7777-777777777777", nombre: "Juan Pérez" },
];

const FALLBACK_CATALOGOS: Catalogos = {
  sillones: FALLBACK_SILLONES,
  profesionales: FALLBACK_PROFESIONALES,
  pacientes: FALLBACK_PACIENTES,
};

async function tryGet<T>(path: string): Promise<T | null> {
  try {
    return await request<T>(path);
  } catch (err) {
    // Fallback ante 404/405 o cualquier error de red (endpoints aún no existen en C-05).
    if (err instanceof ApiError) {
      return null;
    }
    return null;
  }
}

export async function cargarCatalogos(): Promise<Catalogos> {
  const [sillones, profesionales, pacientes] = await Promise.all([
    tryGet<Sillon[]>("/api/v1/sillones"),
    tryGet<Profesional[]>("/api/v1/profesionales"),
    tryGet<Paciente[]>("/api/v1/pacientes"),
  ]);
  return {
    sillones: sillones ?? FALLBACK_SILLONES,
    profesionales: profesionales ?? FALLBACK_PROFESIONALES,
    pacientes: pacientes ?? FALLBACK_PACIENTES,
  };
}

const CatalogosContext = createContext<Catalogos>(FALLBACK_CATALOGOS);

export function CatalogosProvider({ children }: { children: ReactNode }): ReactElement {
  const [catalogos, setCatalogos] = useState<Catalogos>(FALLBACK_CATALOGOS);
  useEffect(() => {
    void cargarCatalogos().then(setCatalogos);
  }, []);
  return <CatalogosContext.Provider value={catalogos}>{children}</CatalogosContext.Provider>;
}

export function useCatalogos(): Catalogos {
  return useContext(CatalogosContext);
}