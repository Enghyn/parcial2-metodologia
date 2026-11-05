// Cliente API tipado (sin `any`): envuelve fetch con forma de error única del backend.
import { useAuthStore } from "../../app/AuthContext";
import { parseRetryAfter } from "../rateLimit";

export interface ApiErrorShape {
  error: { code: string; message: string; details?: unknown };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryAfterSegundos: number | null;

  constructor(status: number, code: string, message: string, retryAfterSegundos: number | null = null) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfterSegundos = retryAfterSegundos;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = useAuthStore.getState().accessToken;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token !== null) {
    headers.Authorization = `Bearer ${token}`;
  }
  const resp = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!resp.ok) {
    const body = (await resp.json().catch(() => null)) as ApiErrorShape | null;
    const retryHeader = resp.headers.get("Retry-After");
    const retryAfterSegundos = parseRetryAfter(retryHeader);
    throw new ApiError(resp.status, body?.error.code ?? "error", body?.error.message ?? "Error de red", retryAfterSegundos);
  }
  return (await resp.json()) as T;
}

export interface HealthResponse {
  status: string;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}
