import { Icon } from "@iconify/react";
import styles from "./ConfirmModal.module.scss";

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmModal = ({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  onConfirm,
  onCancel,
}: Props) => {
  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.title}>{title}</h2>
          <button onClick={onCancel} className={styles.closeBtn}>
            <Icon icon="ph:x" width={16} height={16} />
          </button>
        </div>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button onClick={onCancel} className={styles.cancelBtn}>
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`${styles.confirmBtn} ${danger ? styles.danger : ""}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
