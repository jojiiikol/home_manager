import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CalendarDays,
  Home,
  KeyRound,
  Pencil,
  Plus,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { housesApi } from "../../api/houses";
import { usersApi } from "../../api/users";
import { errorText } from "../../api/client";
import { useAuth } from "../../auth/AuthProvider";
import { ErrorMessage, Loading, Notice } from "../../components/Feedback";
import { FormModal } from "../../components/Modal";
import { passwordFields } from "../../components/Fields";
import {
  formatDate,
  initials,
  roleLabels,
  statusLabels,
  type HouseListItem,
} from "../../types/models";
import { HouseAccessModal } from "../houses/HouseAccessModal";
export function ProfilePage() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [houses, setHouses] = useState<HouseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState<
    "profile" | "password" | "create" | "join" | null
  >(null);
  const name = user!.additional_info.name || user!.username;
  const load = () => {
    setError("");
    setLoading(true);
    housesApi
      .list()
      .then(setHouses)
      .catch((reason) => setError(errorText(reason)))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">ЛИЧНЫЙ КАБИНЕТ</span>
          <h1>Мой профиль</h1>
          <p>Ваше пространство и люди, с которыми вы дома.</p>
        </div>
        <span className="heading-icon">
          <Home size={28} strokeWidth={1.4} />
        </span>
      </div>
      {notice && <Notice>{notice}</Notice>}
      <div className="profile-layout">
        <aside className="profile-card panel">
          <div className="profile-cover">
            <div className="cover-line" />
          </div>
          <div className="profile-content">
            <div className="avatar large">{initials(name)}</div>
            <h2>{name}</h2>
            <p className="username">@{user!.username}</p>
            <div className="profile-meta">
              <CalendarDays size={18} />
              <div>
                <span>С нами с</span>
                <strong>{formatDate(user!.created_at)}</strong>
              </div>
            </div>
            <div className="profile-actions">
              <button
                className="button secondary"
                onClick={() => setModal("profile")}
              >
                <Pencil size={16} />
                Изменить информацию
              </button>
              <button
                className="text-button"
                onClick={() => setModal("password")}
              >
                <KeyRound size={16} />
                Сменить пароль
              </button>
            </div>
          </div>
        </aside>
        <section className="houses-section">
          <div className="section-heading">
            <div>
              <h2>
                Мои дома <span className="count">{houses.length}</span>
              </h2>
              <p>Всё начинается с людей рядом.</p>
            </div>
            <div className="section-actions">
              <button
                className="button secondary"
                onClick={() => setModal("join")}
              >
                <UsersRound size={17} />
                Присоединиться
              </button>
              <button
                className="button primary"
                onClick={() => setModal("create")}
              >
                <Plus size={18} />
                Создать дом
              </button>
            </div>
          </div>
          <ErrorMessage message={error} />
          {error && (
            <button className="text-button" onClick={load}>
              Повторить загрузку
            </button>
          )}
          {loading ? (
            <Loading label="Загружаем ваши дома…" />
          ) : (
            !error &&
            (houses.length ? (
              <div className="house-grid">
                {houses.map((house, index) => (
                  <Link
                    to={`/houses/${house.id}`}
                    className={`house-card panel house-tone-${index % 3}`}
                    key={house.id}
                  >
                    <div className="house-card-top">
                      <div className="house-symbol">
                        <Home size={27} strokeWidth={1.5} />
                      </div>
                      <span className={`badge ${house.participation.status}`}>
                        {statusLabels[house.participation.status]}
                      </span>
                    </div>
                    <h3>{house.additional_info.name}</h3>
                    <span className="identifier">#{house.login}</span>
                    <div className="house-card-footer">
                      <span>
                        {house.participation.role === "admin" ? (
                          <ShieldCheck size={15} />
                        ) : (
                          <UsersRound size={15} />
                        )}
                        {roleLabels[house.participation.role]}
                      </span>
                      <span>Открыть дом</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="empty-houses panel">
                <span className="empty-symbol">
                  <Home size={38} strokeWidth={1.2} />
                </span>
                <h3>Здесь будет ваш дом</h3>
                <p>
                  Создайте свой или присоединитесь к близким.
                  <br />У каждого дома — своё общее пространство.
                </p>
                <button
                  className="button primary"
                  onClick={() => setModal("create")}
                >
                  <Plus size={18} />
                  Создать первый дом
                </button>
              </div>
            ))
          )}
          <div className="house-tip">
            <ShieldCheck size={20} />
            <p>
              Дом — общее пространство. Для вступления нужны его идентификатор и
              пароль от администратора.
            </p>
          </div>
        </section>
      </div>
      {modal === "profile" && (
        <FormModal
          title="Информация о себе"
          description="Как к вам обращаться? Участники дома будут видеть это имя."
          fields={[
            {
              name: "name",
              label: "Ваше имя",
              defaultValue: user!.additional_info.name || "",
              maxLength: 100,
              autoComplete: "name",
              required: false,
              hint: "Если оставить поле пустым, будет отображаться ваш логин.",
            },
          ]}
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            await usersApi.update(data.name.trim() || null);
            await refresh();
            setNotice("Информация о себе обновлена.");
          }}
        />
      )}
      {modal === "password" && (
        <FormModal
          title="Сменить пароль"
          description="Введите текущий пароль и дважды — новый."
          fields={passwordFields(true)}
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            await usersApi.password(data);
            setNotice("Пароль изменён. Используйте его при следующем входе.");
          }}
        />
      )}
      {(modal === "create" || modal === "join") && (
        <HouseAccessModal
          mode={modal}
          onClose={() => setModal(null)}
          onSuccess={(id) => navigate(`/houses/${id}`)}
        />
      )}
    </>
  );
}
