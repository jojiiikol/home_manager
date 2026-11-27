import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CalendarDays,
  Home,
  KeyRound,
  LogOut,
  Pencil,
  Search,
  ShieldCheck,
} from "lucide-react";
import { housesApi } from "../../api/houses";
import { errorText } from "../../api/client";
import { ErrorMessage, Loading, Notice } from "../../components/Feedback";
import { ConfirmModal, FormModal } from "../../components/Modal";
import { houseLoginField, passwordFields } from "../../components/Fields";
import {
  formatDate,
  initials,
  roleLabels,
  statusLabels,
  type House,
  type Participant,
} from "../../types/models";
import { HouseAccessModal } from "./HouseAccessModal";
import { ParticipantModal } from "./ParticipantModal";
export function HousePage() {
  const { id = "" } = useParams();
  const [house, setHouse] = useState<House | null>(null);
  const [me, setMe] = useState<Participant | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState<
    "edit" | "password" | "leave" | "join" | null
  >(null);
  const [selected, setSelected] = useState<Participant | null>(null);
  const load = useCallback(async () => {
    setError("");
    try {
      const [home, participation] = await Promise.all([
        housesApi.get(id),
        housesApi.me(id),
      ]);
      setHouse(home);
      setMe(participation);
      if (participation.status === "active")
        setParticipants(await housesApi.participants(id));
      else setParticipants([]);
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    setLoading(true);
    setHouse(null);
    setMe(null);
    setParticipants([]);
    setSelected(null);
    setNotice("");
    void load();
  }, [load]);
  const isActive = me?.status === "active";
  const isAdmin = isActive && me?.role === "admin";
  const activeAdmins = participants.filter(
    (person) => person.role === "admin" && person.status === "active",
  ).length;
  const lastAdmin = isAdmin && activeAdmins === 1;
  const visible = participants.filter((person) =>
    `${person.name || ""} ${person.username}`
      .toLocaleLowerCase()
      .includes(search.toLocaleLowerCase()),
  );
  if (loading) return <Loading label="Открываем дом…" />;
  if (!house || !me)
    return (
      <>
        <Link className="back-link" to="/profile">
          Мой профиль / Дома
        </Link>
        <ErrorMessage message={error || "Дом недоступен"} />
        <button className="button secondary" onClick={() => void load()}>
          Повторить загрузку
        </button>
      </>
    );
  return (
    <>
      <Link to="/profile" className="back-link">
        Мой профиль <span>/</span> Мои дома
      </Link>
      <section className="house-hero panel">
        <div className="house-hero-main">
          <span className="house-hero-icon">
            <Home size={36} strokeWidth={1.4} />
          </span>
          <div>
            <span className="eyebrow">ОБЩЕЕ ПРОСТРАНСТВО</span>
            <h1>{house.additional_info.name}</h1>
            <span className="identifier">Идентификатор · {house.login}</span>
          </div>
        </div>
        <div className="house-hero-bottom">
          <div className="house-hero-meta">
            <span>
              <CalendarDays size={16} />
              Создан {formatDate(house.created_at)}
            </span>
            <span className={`badge ${me.status}`}>
              {statusLabels[me.status]}
            </span>
            <span className="badge neutral">{roleLabels[me.role]}</span>
          </div>
          {isAdmin && (
            <div className="section-actions">
              <button
                className="button secondary"
                onClick={() => setModal("edit")}
              >
                <Pencil size={16} />
                Изменить информацию
              </button>
              <button
                className="button secondary"
                onClick={() => setModal("password")}
              >
                <KeyRound size={16} />
                Сменить пароль
              </button>
            </div>
          )}
        </div>
      </section>
      {notice && <Notice>{notice}</Notice>}
      <ErrorMessage message={error} />
      {error && (
        <button className="text-button" onClick={() => void load()}>
          Обновить данные
        </button>
      )}
      {isActive ? (
        <section className="participants-section panel">
          <div className="section-heading">
            <div>
              <h2>
                Люди дома <span className="count">{participants.length}</span>
              </h2>
              <p>Те, кто делает это место домом.</p>
            </div>
            <label className="search-box">
              <Search size={17} />
              <input
                aria-label="Поиск участников"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Найти участника"
              />
            </label>
          </div>
          <div className="participant-table-heading" aria-hidden="true">
            <span>Участник</span>
            <span>Роль</span>
            <span>Статус</span>
            <span>В доме с</span>
          </div>
          <ul className="participant-list">
            {visible.map((person) => (
              <li key={person.id}>
                <button
                  className="participant-row"
                  onClick={() => setSelected(person)}
                >
                  <span className="person-name">
                    <span className="avatar small">
                      {initials(person.name || person.username)}
                    </span>
                    <span>
                      <strong>{person.name || person.username}</strong>
                      {person.user_id === me.user_id && <small>Это вы</small>}
                    </span>
                  </span>
                  <span className="person-role">
                    {person.role === "admin" && <ShieldCheck size={15} />}
                    {roleLabels[person.role]}
                  </span>
                  <span className="person-status">
                    <span className={`badge ${person.status}`}>
                      {statusLabels[person.status]}
                    </span>
                  </span>
                  <span className="person-date">
                    {formatDate(person.created_at)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {!visible.length && (
            <p className="search-empty">
              Никого не нашли. Попробуйте другое имя или логин.
            </p>
          )}
        </section>
      ) : (
        <section className="inactive-panel panel">
          <span className="empty-symbol">
            <ShieldCheck size={30} strokeWidth={1.4} />
          </span>
          <h2>
            {me.status === "blocked"
              ? "Ваше участие заблокировано"
              : "Вы вышли из этого дома"}
          </h2>
          <p>
            {me.status === "blocked"
              ? "Информация о доме остаётся доступной. Для восстановления участия обратитесь к администратору."
              : "Вы по-прежнему можете видеть информацию о доме. Чтобы вернуться, введите действующий пароль дома."}
          </p>
          {me.status === "left" && (
            <button className="button primary" onClick={() => setModal("join")}>
              Вернуться в дом
            </button>
          )}
        </section>
      )}
      <div className="membership-footer">
        <span>Вы присоединились {formatDate(me.created_at)}</span>
        {isActive && (
          <button
            className="text-button muted-danger"
            disabled={lastAdmin}
            title={
              lastAdmin
                ? "Сначала назначьте другого активного администратора"
                : undefined
            }
            onClick={() => setModal("leave")}
          >
            <LogOut size={16} />
            Выйти из дома
          </button>
        )}
      </div>
      {lastAdmin && (
        <p className="last-admin-note">
          Вы — единственный активный администратор. Перед выходом назначьте
          другого.
        </p>
      )}
      {modal === "edit" && (
        <FormModal
          title="Информация о доме"
          description="Название видят участники. Идентификатор нужен, чтобы присоединиться к дому."
          fields={[
            {
              name: "name",
              label: "Название дома",
              defaultValue: house.additional_info.name,
              maxLength: 100,
            },
            { ...houseLoginField, defaultValue: house.login },
          ]}
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            await housesApi.update(id, data);
            await load();
            setNotice("Информация о доме обновлена.");
          }}
        />
      )}
      {modal === "password" && (
        <FormModal
          title="Пароль дома"
          description="Новый пароль понадобится для вступления. Текущие участники сохранят доступ."
          fields={passwordFields(true)}
          onClose={() => setModal(null)}
          onSubmit={async (data) => {
            await housesApi.password(id, data);
            setNotice("Пароль дома изменён.");
          }}
        />
      )}
      {modal === "leave" && (
        <ConfirmModal
          title="Выйти из дома?"
          description="Вы сохраните доступ к информации о доме. Чтобы вернуться, потребуется действующий пароль."
          label="Выйти из дома"
          onClose={() => setModal(null)}
          onConfirm={async () => {
            await housesApi.leave(id);
            await load();
            setNotice("Вы вышли из дома.");
          }}
        />
      )}
      {modal === "join" && (
        <HouseAccessModal
          mode="join"
          login={house.login}
          onClose={() => setModal(null)}
          onSuccess={() => {
            void load();
            setNotice("Добро пожаловать домой!");
          }}
        />
      )}
      {selected && (
        <ParticipantModal
          key={selected.id}
          participant={selected}
          isAdmin={Boolean(isAdmin)}
          lastAdmin={
            selected.status === "active" &&
            selected.role === "admin" &&
            activeAdmins === 1
          }
          onClose={() => setSelected(null)}
          onChanged={async () => {
            await load();
            setNotice("Данные участника обновлены.");
          }}
        />
      )}
    </>
  );
}
