import {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  type ReactNode,
} from "react";
import { Navigate, Outlet, useNavigate } from "react-router-dom";
import { ApiError, AUTH_EXPIRED, errorText, tokenStore } from "../api/client";
import { usersApi } from "../api/users";
import type { User } from "../types/models";
import { Loading } from "../components/Feedback";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | null>(null);
function tokenExpiry(token: string): number {
  try {
    const payload = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    );
    return typeof payload.exp === "number" ? payload.exp * 1000 : 0;
  } catch {
    return 0;
  }
}
export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const navigateRef = useRef(navigate);
  useEffect(() => {
    navigateRef.current = navigate;
  }, [navigate]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const logout = () => {
    tokenStore.clear();
    setUser(null);
    setError("");
    navigate("/auth", { replace: true });
  };
  const refresh = async () => {
    const token = tokenStore.get();
    const profile = await usersApi.me();
    if (token && tokenStore.get() === token) {
      setUser(profile);
      setError("");
    }
  };
  const login = async (username: string, password: string) => {
    const data = await usersApi.login(username, password);
    tokenStore.set(data.access_token);
    try {
      await refresh();
    } catch (error) {
      tokenStore.clear();
      throw error;
    }
  };
  useEffect(() => {
    let live = true;
    const token = tokenStore.get();
    const expire = () => {
      tokenStore.clear();
      setUser(null);
      setError("");
      navigateRef.current("/auth?expired=1", { replace: true });
    };
    window.addEventListener(AUTH_EXPIRED, expire);
    if (!token) setLoading(false);
    else if (tokenExpiry(token) <= Date.now()) {
      expire();
      setLoading(false);
    } else
      usersApi
        .me()
        .then((value) => {
          if (live && tokenStore.get() === token) setUser(value);
        })
        .catch((reason) => {
          if (live && !(reason instanceof ApiError && reason.status === 401))
            setError(errorText(reason));
        })
        .finally(() => {
          if (live) setLoading(false);
        });
    return () => {
      live = false;
      window.removeEventListener(AUTH_EXPIRED, expire);
    };
  }, []);
  useEffect(() => {
    const token = tokenStore.get();
    if (!user || !token) return;
    const remaining = tokenExpiry(token) - Date.now();
    const timer = window.setTimeout(
      () => window.dispatchEvent(new Event(AUTH_EXPIRED)),
      Math.max(0, remaining),
    );
    const check = () => {
      if (tokenExpiry(token) <= Date.now())
        window.dispatchEvent(new Event(AUTH_EXPIRED));
    };
    window.addEventListener("focus", check);
    document.addEventListener("visibilitychange", check);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("focus", check);
      document.removeEventListener("visibilitychange", check);
    };
  }, [user]);
  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider is missing");
  return value;
}
export function ProtectedRoute() {
  const { user, loading, error } = useAuth();
  if (loading) return <Loading label="Открываем ваш кабинет…" />;
  if (error && !user)
    return (
      <main className="startup-error">
        <h1>Не удалось загрузить профиль</h1>
        <p role="alert">{error}</p>
        <button
          className="button primary"
          onClick={() => window.location.reload()}
        >
          Попробовать ещё раз
        </button>
      </main>
    );
  return user ? <Outlet /> : <Navigate to="/auth" replace />;
}
