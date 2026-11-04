// Cliente tipado para auth (login + perfil), reusando request<T> de client.ts (R7, R8).
import { request } from "./client";

export interface LoginInput {
  email: string;
  password: string;
}

export interface TokenOut {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface UsuarioPerfil {
  id: string;
  nombre: string;
  email: string;
  rol: "admin" | "recepcion" | "odontologo";
}

export function login(input: LoginInput): Promise<TokenOut> {
  return request<TokenOut>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function me(): Promise<UsuarioPerfil> {
  return request<UsuarioPerfil>("/api/v1/auth/me");
}