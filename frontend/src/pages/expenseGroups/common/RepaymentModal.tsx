import { Icon } from "@iconify/react";
import styles from "./RepaymentModal.module.scss";
import { NewRepaymentPayload, TransactionWithUserInfo } from "@/types";
import { useState } from "react";
import { useCreateRepayment } from "@/hooks/queries";
import { DatePicker } from "@/components/ui/DatePicker";
import { displayName } from "@/utils/user";
import { getErrorMessage } from "@/utils/error";

interface Props {
  transaction: TransactionWithUserInfo;
  expense_group_id: number;
  onClose: () => void;
}

const initialResolveState = {
  note: "",
  paid_at: null,
};

export const RepaymentModal = ({
  transaction,
  onClose,
  expense_group_id,
}: Props) => {
  const [form, setForm] =
    useState<Partial<NewRepaymentPayload>>(initialResolveState);

  const {
    mutate: createRepayment,
    isPending: createRepaymentPending,
    error: createRepaymentError,
  } = useCreateRepayment();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    createRepayment(
      {
        id: expense_group_id,
        data: {
          amount: transaction.amount,
          note: form.note?.trim() || undefined,
          from_user_id: transaction.from_user_id,
          to_user_id: transaction.to_user_id,
          paid_at: form.paid_at
            ? new Date(form.paid_at).toISOString()
            : undefined,
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
          <h2 className={styles.modalTitle}>Confirm payment</h2>
          <button
            onClick={onClose}
            className={styles.closeBtn}
            disabled={!!createRepaymentPending}
          >
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form
          id="repayment-form"
          onSubmit={handleSubmit}
          className={styles.form}
        >
          <div className={styles.fields}>
            <p className={styles.confirmText}>
              {`${displayName(transaction.from_user)} has paid ${displayName(transaction.to_user)} €${transaction.amount.toFixed(2)}.`}
            </p>
            <div className={styles.field}>
              <label className={styles.label}>Paid at</label>
              <DatePicker
                value={form.paid_at ?? null}
                onChange={(v) => setForm({ ...form, paid_at: v })}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Note</label>
              <textarea
                className={styles.input}
                value={form.note ?? ""}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
                rows={3}
                placeholder="Optional note"
              />
            </div>
          </div>

          {createRepaymentError && (
            <div className={styles.errorBanner}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {getErrorMessage(
                createRepaymentError,
                "Failed to resolve payment. Please try again.",
              )}
            </div>
          )}

          <div className={styles.formActions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelBtn}
              disabled={!!createRepaymentPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={!!createRepaymentPending}
            >
              Confirm
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
