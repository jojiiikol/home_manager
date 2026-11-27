import { Home, LogOut, UserRound } from "lucide-react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { initials } from "../types/models";
export function Brand() {
  return (
    <Link to="/profile" className="brand" aria-label="Дома — на главную">
      <span className="brand-mark">
        <Home size={23} strokeWidth={1.8} />
      </span>
      <span>
        дома<span className="brand-dot">.</span>
      </span>
    </Link>
  );
}
export function Layout() {
  const { user, logout } = useAuth();
  const name = user!.additional_info.name || user!.username;
  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-inner">
          <Brand />
          <span className="header-caption">Домашний менеджер</span>
          <nav aria-label="Основная навигация">
            <Link
              className="profile-link"
              to="/profile"
              aria-label="Мой профиль"
            >
              <span className="small-avatar">{initials(name)}</span>
              <span>{name}</span>
              <UserRound size={17} />
            </Link>
            <button
              className="icon-button logout"
              onClick={logout}
              aria-label="Выйти из аккаунта"
              title="Выйти из аккаунта"
            >
              <LogOut size={19} />
            </button>
          </nav>
        </div>
      </header>
      <main className="main-container">
        <Outlet />
      </main>
      <footer className="app-footer">
        <span>Дома — там, где ваши люди.</span>
        <span>Домашний менеджер</span>
      </footer>
    </div>
  );
}
