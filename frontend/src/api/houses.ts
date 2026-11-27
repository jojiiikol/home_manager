import { request } from "./client";
import type {
  House,
  HouseListItem,
  Participant,
  Role,
  Status,
} from "../types/models";
export const housesApi = {
  list: () => request<HouseListItem[]>("/houses"),
  get: (id: string) => request<House>(`/houses/${id}`),
  create: (body: Record<string, string>) =>
    request<House>("/houses", { method: "POST", body }),
  join: (body: Record<string, string>) =>
    request<Participant>("/houses/join", { method: "POST", body }),
  me: (id: string) => request<Participant>(`/houses/${id}/participants/me`),
  participants: (id: string) =>
    request<Participant[]>(`/houses/${id}/participants`),
  update: (id: string, body: Record<string, string>) =>
    request<House>(`/houses/${id}`, { method: "PATCH", body }),
  password: (id: string, body: Record<string, string>) =>
    request<void>(`/houses/${id}/password`, { method: "PUT", body }),
  leave: (id: string) =>
    request<Participant>(`/houses/${id}/leave`, { method: "POST" }),
  participant: (
    house: string,
    user: string,
    body: { role?: Role; status?: Status },
  ) =>
    request<Participant>(`/houses/${house}/participants/${user}`, {
      method: "PATCH",
      body,
    }),
};
