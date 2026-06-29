import api from "./client";
import type { User } from "../types/api";

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/users/me");
  return data;
}
