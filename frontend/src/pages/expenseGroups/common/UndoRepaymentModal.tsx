import { Icon } from "@iconify/react";
import styles from "./UndoRepaymentModal.module.scss";
import { Repayment, UndoRepaymentPayload } from "@/types";
import { useState } from "react";
import { useUndoRepayment } from "@/hooks/queries";
import { displayName } from "@/utils/user";
import { getErrorMessage } from "@/utils/error";

interface Props {
  repayment: Repayment;
  expense_group_id: number;
  onClose: () => void;
}

const initialResolveState = {
  deleted_note: "",
};

export const UndoRepaymentModal = ({
  repayment,
  onClose,
  expense_group_id,
}: Props) => {
  const [form, setForm] =
    useState<Partial<UndoRepaymentPayload>>(initialResolveState);

  const {
    mutate: undoRepayment,
    isPending: undoRepaymentPending,
    error: undoRepaymentError,
  } = useUndoRepayment();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    undoRepayment(
      {
        id: expense_group_id,
        repayment_id: repayment.id,
        data: {
          deleted_note: form.deleted_note?.trim() || undefined,
        },
      },
      {
        onSuccess: () => onClose(),
      },
    );
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Confirm undone</h2>
          <button
            onClick={onClose}
            className={styles.closeBtn}
            disabled={!!undoRepaymentPending}
          >
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form
          id="undo-repayment-form"
          onSubmit={handleSubmit}
          className={styles.form}
        >
          <div className={styles.fields}>
            <p className={styles.confirmText}>
              <b>Undo payment: </b>
              {`${displayName(repayment.from_user)} has paid ${displayName(repayment.to_user)} €${repayment.amount.toFixed(2)}.`}
            </p>
            <div className={styles.field}>
              <label className={styles.label}>Note</label>
              <textarea
                className={styles.input}
                value={form.deleted_note ?? ""}
                onChange={(e) =>
                  setForm({ ...form, deleted_note: e.target.value })
                }
                rows={3}
                placeholder="Optional note"
              />
            </div>
          </div>

          {undoRepaymentError && (
            <div className={styles.errorBanner}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {getErrorMessage(
                undoRepaymentError,
                "Failed to undo repayment. Please try again.",
              )}
            </div>
          )}

          <div className={styles.formActions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelBtn}
              disabled={!!undoRepaymentPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={!!undoRepaymentPending}
            >
              Undone
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
