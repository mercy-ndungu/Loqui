import api from "./client";
import type { AuthMessageResponse } from "../types/api";
import { initCsrfToken } from "../utils/security";

export async function login(email: string, password: string): Promise<AuthMessageResponse> {
  await initCsrfToken();
  const { data } = await api.post<AuthMessageResponse>("/auth/login", { email, password });
  return data;
}

export async function signup(
  email: string,
  password: string,
  full_name: string,
): Promise<AuthMessageResponse> {
  await initCsrfToken();
  const { data } = await api.post<AuthMessageResponse>("/auth/signup", {
    email,
    password,
    full_name,
  });
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
