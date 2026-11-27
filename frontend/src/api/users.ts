import { request } from "./client";
import type { PublicUser, Token, User } from "../types/models";
export const usersApi = {
  register: (body: Record<string, string>) =>
    request<User>("/users", { method: "POST", body, publicRequest: true }),
  login: (username: string, password: string) =>
    request<Token>("/auth/token", {
      method: "POST",
      body: { username, password },
      publicRequest: true,
    }),
  me: () => request<User>("/users/me"),
  get: (id: string) => request<PublicUser>(`/users/${id}`),
  update: (name: string | null) =>
    request<User>("/users/me", { method: "PATCH", body: { name } }),
  password: (body: Record<string, string>) =>
    request<void>("/users/me/password", { method: "PUT", body }),
};
