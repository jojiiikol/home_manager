import { useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import {
  Home,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { usersApi } from "../../api/users";
import { errorText } from "../../api/client";
import { useAuth } from "../../auth/AuthProvider";
import {
  Field,
  passwordFields,
  readForm,
  usernameField,
  validateMatches,
} from "../../components/Fields";
import { ErrorMessage, Loading } from "../../components/Feedback";
import { Brand } from "../../components/Layout";
export function AuthPage() {
  const { user, login, loading } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [registered, setRegistered] = useState(false);
  const fields = [
    usernameField,
    ...(register
      ? passwordFields()
      : [
          {
            name: "password",
            label: "Пароль",
            type: "password",
            autoComplete: "current-password",
            minLength: 1,
            maxLength: 128,
          },
        ]),
  ];
  if (loading) return <Loading />;
  if (user) return <Navigate to="/profile" replace />;
  return (
    <main className="auth-page">
      <section className="auth-story">
        <Brand />
        <div className="story-content">
          <span className="eyebrow">МЕСТО ДЛЯ ВАШЕГО ДОМА</span>
          <h1>
            Ближе к дому.
            <br />
            Ближе друг к другу.
          </h1>
          <p>
            Общее пространство для вас и людей,
            <br className="desktop-only" /> с которыми вы делите повседневность.
          </p>
          <div className="house-art" aria-hidden="true">
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <div className="art-tile tile-back">
              <UsersRound />
            </div>
            <div className="art-home">
              <Home strokeWidth={1} />
              <span>У каждого дома — свои люди</span>
              <div className="art-people">
                <i>С</i>
                <i>А</i>
                <i>М</i>
              </div>
            </div>
            <div className="art-tile tile-front">
              <KeyRound />
            </div>
          </div>
        </div>
        <div className="story-footer">
          <ShieldCheck size={18} />
          <span>Ваш дом. Ваше личное пространство.</span>
        </div>
      </section>
      <section className="auth-form-section">
        <div className="auth-card">
          <div className="auth-mobile-brand">
            <Brand />
          </div>
          <div className="auth-tabs" aria-label="Вход или регистрация">
            <button
              aria-pressed={!register}
              onClick={() => {
                setRegister(false);
                setError("");
              }}
            >
              {"Вход"}
            </button>
            <button
              aria-pressed={register}
              onClick={() => {
                setRegister(true);
                setError("");
              }}
            >
              {"Регистрация"}
            </button>
          </div>
          <h2>
            {register ? "Добро пожаловать домой" : "Рады видеть вас снова"}
          </h2>
          <p className="auth-subtitle">
            {register
              ? "Создайте аккаунт и соберите своих людей в одном месте."
              : "Войдите, чтобы открыть свой профиль и дома."}
          </p>
          {params.has("expired") && (
            <p className="inline-note">
              Время сессии истекло. Войдите ещё раз.
            </p>
          )}
          {registered && (
            <p className="inline-note">
              Аккаунт создан. Войдите с указанным паролем.
            </p>
          )}
          <form
            key={register ? "register" : "login"}
            onSubmit={async (event) => {
              event.preventDefault();
              if (busy) return;
              setError("");
              const data = readForm(event.currentTarget);
              try {
                validateMatches(fields, data);
                setBusy(true);
                if (register) {
                  await usersApi.register(data);
                  setRegistered(true);
                  setRegister(false);
                } else {
                  await login(data.username, data.password);
                  navigate("/profile", { replace: true });
                }
              } catch (reason) {
                setError(errorText(reason));
              } finally {
                setBusy(false);
              }
            }}
          >
            <fieldset disabled={busy}>
              {fields.map((field) => (
                <Field key={field.name} {...field} />
              ))}
            </fieldset>
            <ErrorMessage message={error} />
            <button className="button primary auth-submit" disabled={busy}>
              {busy && <LoaderCircle size={18} className="spin" />}
              {register ? "Создать аккаунт" : "Войти"}
            </button>
          </form>
          <div className="auth-bottom">
            <ShieldCheck size={16} />
            <span>Доступ к вашим домам — только по аккаунту</span>
          </div>
        </div>
        <p className="auth-copyright">
          Простые вещи, которые делают нас ближе.
        </p>
      </section>
    </main>
  );
}
