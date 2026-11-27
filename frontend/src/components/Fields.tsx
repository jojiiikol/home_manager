import { useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
export interface FieldSpec {
  name: string;
  label: string;
  type?: string;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  hint?: string;
  autoComplete?: string;
  defaultValue?: string;
  matches?: string;
}
export function Field({
  label,
  hint,
  type = "text",
  matches: _matches,
  ...props
}: FieldSpec) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="input-wrap">
        <input
          id={id}
          aria-describedby={hint ? `${id}-hint` : undefined}
          type={type === "password" && visible ? "text" : type}
          {...props}
          required={props.required ?? true}
        />
        {type === "password" && (
          <button
            type="button"
            className="password-toggle"
            aria-label={visible ? `Скрыть: ${label}` : `Показать: ${label}`}
            onClick={() => setVisible(!visible)}
          >
            {visible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
      {hint && (
        <p id={`${id}-hint`} className="field-hint">
          {hint}
        </p>
      )}
    </div>
  );
}
export const usernameField: FieldSpec = {
  name: "username",
  label: "Логин",
  minLength: 3,
  maxLength: 64,
  pattern: "[a-zA-Z0-9_.\\-]+",
  autoComplete: "username",
  hint: "От 3 символов: латинские буквы, цифры, точка, дефис и _",
};
export const houseLoginField: FieldSpec = {
  ...usernameField,
  name: "login",
  label: "Идентификатор дома",
  autoComplete: "off",
};
export const passwordFields = (change = false): FieldSpec[] => [
  ...(change
    ? [
        {
          name: "old_password",
          label: "Текущий пароль",
          type: "password",
          autoComplete: "current-password",
          maxLength: 128,
        },
      ]
    : []),
  {
    name: change ? "new_password" : "password",
    label: change ? "Новый пароль" : "Пароль",
    type: "password",
    minLength: 8,
    maxLength: 128,
    autoComplete: "new-password",
    hint: "От 8 до 128 символов",
  },
  {
    name: change ? "new_password_confirmation" : "password_confirmation",
    label: "Повторите пароль",
    type: "password",
    minLength: 8,
    maxLength: 128,
    autoComplete: "new-password",
    matches: change ? "new_password" : "password",
  },
];
export function readForm(form: HTMLFormElement) {
  return Object.fromEntries(new FormData(form).entries()) as Record<
    string,
    string
  >;
}
export function validateMatches(
  fields: FieldSpec[],
  data: Record<string, string>,
) {
  if (
    fields.some(
      (field) => field.matches && data[field.name] !== data[field.matches],
    )
  )
    throw new Error("Пароли не совпадают. Проверьте оба поля.");
}
