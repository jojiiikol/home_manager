export interface User {
  id: string;
  username: string;
  additional_info: { name: string | null };
  created_at: string;
  updated_at: string;
}
export type PublicUser = Omit<User, "id">;
export type Role = "admin" | "member";
export type Status = "active" | "blocked" | "left";
export interface Participant {
  id: string;
  house_id: string;
  user_id: string;
  username: string;
  name: string | null;
  role: Role;
  status: Status;
  created_at: string;
  updated_at: string;
}
export interface House {
  id: string;
  login: string;
  additional_info: { name: string };
  created_at: string;
  updated_at: string;
}
export interface HouseListItem extends House {
  participation: Participant;
}
export interface Token {
  access_token: string;
  expires_in: number;
  token_type: string;
}
export const roleLabels: Record<Role, string> = {
  admin: "Администратор",
  member: "Участник",
};
export const statusLabels: Record<Status, string> = {
  active: "Активен",
  blocked: "Заблокирован",
  left: "Вышел из дома",
};
export function formatDate(value: string) {
  // PostgreSQL возвращает UTC; naive даты из тестового SQLite тоже трактуем как UTC.
  const date = new Date(
    /(?:Z|[+-]\d\d:\d\d)$/.test(value) ? value : `${value}Z`,
  );
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}
export function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}
