const TOKEN_KEY = "home-manager.token";
export const AUTH_EXPIRED = "home-manager:auth-expired";
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (value: string) => sessionStorage.setItem(TOKEN_KEY, value),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};
const messages: Record<string, string> = {
  "Username already exists": "Этот логин уже занят. Выберите другой.",
  "Invalid username or password": "Неверный логин или пароль.",
  "Invalid or expired credentials": "Сессия завершена. Войдите ещё раз.",
  "Incorrect old password": "Текущий пароль указан неверно.",
  "House login already exists": "Этот идентификатор дома уже занят.",
  "Invalid house login or password": "Неверный идентификатор или пароль дома.",
  "House access denied":
    "Действие недоступно. Проверьте свой статус и права в доме.",
  "Already a house participant": "Вы уже состоите в этом доме.",
  "House must have at least one active admin":
    "В доме должен остаться хотя бы один активный администратор. Сначала назначьте другого.",
  "Incorrect old house password": "Текущий пароль дома указан неверно.",
  "House not found": "Дом не найден.",
  "User not found": "Пользователь не найден.",
  "Participant not found": "Участник не найден в этом доме.",
  "Restore participant first; change role separately":
    "Сначала восстановите участника, затем измените его роль.",
};
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
interface ValidationIssue {
  msg: string;
  type: string;
  loc: (string | number)[];
}
function errorMessage(detail: unknown): string {
  if (typeof detail === "string") return messages[detail] || detail;
  if (Array.isArray(detail)) {
    const issues = detail as ValidationIssue[];
    if (issues.some((issue) => issue.msg.includes("Пароли не совпадают")))
      return "Пароли не совпадают. Проверьте оба поля.";
    if (issues.some((issue) => issue.type === "missing"))
      return "Заполните все обязательные поля, включая повтор пароля.";
    if (
      issues.some((issue) =>
        issue.loc.some((field) => String(field).includes("password")),
      )
    )
      return "Пароль должен содержать от 8 до 128 символов.";
    if (issues.some((issue) => issue.type === "string_pattern_mismatch"))
      return "Используйте латинские буквы, цифры, точку, дефис или подчёркивание.";
    return "Проверьте заполненные поля и попробуйте ещё раз.";
  }
  return "Не удалось выполнить действие. Попробуйте ещё раз.";
}
export async function request<T>(
  path: string,
  {
    method = "GET",
    body,
    publicRequest = false,
  }: { method?: string; body?: unknown; publicRequest?: boolean } = {},
): Promise<T> {
  const token = publicRequest ? null : tokenStore.get();
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      0,
      "Не удалось подключиться к серверу. Проверьте соединение и попробуйте снова.",
    );
  }
  if (response.status === 401 && token) {
    tokenStore.clear();
    window.dispatchEvent(new Event(AUTH_EXPIRED));
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      response.status >= 500
        ? "Сервер временно недоступен. Попробуйте ещё раз."
        : errorMessage(data.detail),
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const errorText = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Что-то пошло не так. Попробуйте ещё раз.";
