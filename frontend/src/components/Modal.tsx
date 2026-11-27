import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { LoaderCircle, X } from "lucide-react";
import { errorText } from "../api/client";
import { ErrorMessage } from "./Feedback";
import { Field, readForm, validateMatches, type FieldSpec } from "./Fields";
export function Modal({
  title,
  description,
  onClose,
  children,
  busy = false,
}: {
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    ref.current?.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <div className="modal-content">
        <div className="modal-heading">
          <div>
            <h2 id={titleId}>{title}</h2>
            {description && <p>{description}</p>}
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="Закрыть"
            disabled={busy}
            onClick={onClose}
          >
            <X size={21} />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
export function FormModal({
  title,
  description,
  fields,
  onSubmit,
  onClose,
  submitLabel = "Сохранить изменения",
}: {
  title: string;
  description?: string;
  fields: FieldSpec[];
  onSubmit: (data: Record<string, string>) => Promise<void>;
  onClose: () => void;
  submitLabel?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <Modal
      title={title}
      description={description}
      onClose={onClose}
      busy={busy}
    >
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          if (busy) return;
          setError("");
          const data = readForm(event.currentTarget);
          try {
            validateMatches(fields, data);
            setBusy(true);
            await onSubmit(data);
            onClose();
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
        <div className="modal-actions">
          <button
            type="button"
            className="button secondary"
            disabled={busy}
            onClick={onClose}
          >
            Отмена
          </button>
          <button className="button primary" disabled={busy}>
            {busy && <LoaderCircle size={17} className="spin" />}
            {submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
}
export function ConfirmModal({
  title,
  description,
  label,
  onConfirm,
  onClose,
}: {
  title: string;
  description: string;
  label: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <Modal
      title={title}
      description={description}
      onClose={onClose}
      busy={busy}
    >
      <ErrorMessage message={error} />
      <div className="modal-actions">
        <button className="button secondary" disabled={busy} onClick={onClose}>
          Отмена
        </button>
        <button
          className="button danger"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await onConfirm();
              onClose();
            } catch (reason) {
              setError(errorText(reason));
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy && <LoaderCircle className="spin" size={17} />}
          {label}
        </button>
      </div>
    </Modal>
  );
}
