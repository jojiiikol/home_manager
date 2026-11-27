import { useEffect, useState } from "react";
import {
  Ban,
  CalendarDays,
  Check,
  LoaderCircle,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { usersApi } from "../../api/users";
import { housesApi } from "../../api/houses";
import { errorText } from "../../api/client";
import { Modal } from "../../components/Modal";
import { ErrorMessage, Loading } from "../../components/Feedback";
import {
  formatDate,
  initials,
  roleLabels,
  statusLabels,
  type Participant,
  type PublicUser,
  type Role,
  type Status,
} from "../../types/models";
type Action = {
  label: string;
  description: string;
  body: { role?: Role; status?: Status };
  danger?: boolean;
};
export function ParticipantModal({
  participant,
  isAdmin,
  lastAdmin,
  onClose,
  onChanged,
}: {
  participant: Participant;
  isAdmin: boolean;
  lastAdmin: boolean;
  onClose: () => void;
  onChanged: () => Promise<void>;
}) {
  const [profile, setProfile] = useState<PublicUser | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [action, setAction] = useState<Action | null>(null);
  const name = participant.name || participant.username;
  useEffect(() => {
    let live = true;
    usersApi
      .get(participant.user_id)
      .then((value) => {
        if (live) setProfile(value);
      })
      .catch((reason) => {
        if (live) setError(errorText(reason));
      });
    return () => {
      live = false;
    };
  }, [participant.user_id]);
  const changeRole: Action = {
    label:
      participant.role === "admin"
        ? "Сделать участником"
        : "Назначить администратором",
    description:
      participant.role === "admin"
        ? "Участник больше не сможет управлять домом."
        : "Участник получит право менять дом и управлять другими участниками.",
    body: { role: participant.role === "admin" ? "member" : "admin" },
  };
  const block: Action = {
    label: "Заблокировать участника",
    description:
      "Участник сохранит доступ к информации о доме, но не сможет вернуться самостоятельно.",
    body: { status: "blocked" },
    danger: true,
  };
  const restore: Action = {
    label: "Восстановить участие",
    description:
      "Пользователь снова станет активным участником без прав администратора.",
    body: { status: "active" },
  };
  return (
    <Modal title="Участник дома" onClose={onClose} busy={busy}>
      <div className="participant-profile">
        <div className="avatar">{initials(name)}</div>
        <h3>{name}</h3>
        <p>@{participant.username}</p>
        <div className="badge-row">
          <span className="badge neutral">{roleLabels[participant.role]}</span>
          <span className={`badge ${participant.status}`}>
            {statusLabels[participant.status]}
          </span>
        </div>
      </div>
      <div className="detail-list">
        <div>
          <span>
            <CalendarDays size={17} />В доме с
          </span>
          <strong>{formatDate(participant.created_at)}</strong>
        </div>
        {profile ? (
          <>
            <div>
              <span>Регистрация</span>
              <strong>{formatDate(profile.created_at)}</strong>
            </div>
            <div>
              <span>Обновление профиля</span>
              <strong>{formatDate(profile.updated_at)}</strong>
            </div>
          </>
        ) : (
          !error && <Loading label="Загружаем профиль…" />
        )}
      </div>
      <ErrorMessage message={error} />
      {isAdmin && (
        <div className="admin-controls">
          <span className="eyebrow">УПРАВЛЕНИЕ УЧАСТНИКОМ</span>
          {lastAdmin && (
            <p className="inline-note">
              Это последний активный администратор. Сначала назначьте другого.
            </p>
          )}
          {!action ? (
            <div className="admin-button-list">
              {participant.status === "active" ? (
                <>
                  <button
                    className="button secondary"
                    disabled={lastAdmin}
                    onClick={() => setAction(changeRole)}
                  >
                    <ShieldCheck size={17} />
                    {changeRole.label}
                  </button>
                  <button
                    className="button danger-subtle"
                    disabled={lastAdmin}
                    onClick={() => setAction(block)}
                  >
                    <Ban size={17} />
                    {block.label}
                  </button>
                </>
              ) : (
                <button
                  className="button secondary"
                  onClick={() => setAction(restore)}
                >
                  <UserRound size={17} />
                  {restore.label}
                </button>
              )}
            </div>
          ) : (
            <div className="confirm-action">
              <h4>{action.label}?</h4>
              <p>{action.description}</p>
              <div className="modal-actions">
                <button
                  className="button secondary"
                  disabled={busy}
                  onClick={() => setAction(null)}
                >
                  Отмена
                </button>
                <button
                  className={`button ${action.danger ? "danger" : "primary"}`}
                  disabled={busy}
                  onClick={async () => {
                    setError("");
                    setBusy(true);
                    try {
                      await housesApi.participant(
                        participant.house_id,
                        participant.user_id,
                        action.body,
                      );
                      await onChanged();
                      onClose();
                    } catch (reason) {
                      setError(errorText(reason));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {busy ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <Check size={16} />
                  )}
                  Подтвердить
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
