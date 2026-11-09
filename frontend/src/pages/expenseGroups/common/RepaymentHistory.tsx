import styles from "./RepaymentHistory.module.scss";
import { ExpenseGroup, Repayment } from "@/types";
import { useRepayments } from "@/hooks/queries";
import { displayName } from "@/utils/user";
import { useAuthStore } from "@/stores/authStore";
import { UndoRepaymentModal } from "./UndoRepaymentModal";
import { useState } from "react";
import { Icon } from "@iconify/react";

type Props = {
  expense_group: ExpenseGroup;
};

const RepaymentHistory = ({ expense_group }: Props) => {
  const current_user = useAuthStore((s) => s.user);
  const { data: repayments } = useRepayments(expense_group.id);

  const [open, setOpen] = useState(false);
  const [showConfirmUndoRepaymentModal, setShowConfirmUndoRepaymentModal] =
    useState(false);
  const [selectedRepayment, setSelectedRepayment] = useState<Repayment | null>(
    null,
  );

  // Dont show anything if there are no repayments
  if (!repayments || repayments.length === 0) return null;

  const isGroupAdmin = expense_group.members.some(
    (m) => m.user_id === current_user?.id && m.role === "admin",
  );

  const showUndoBtn = (repayment: Repayment) => {
    if (repayment.is_deleted) return false;
    if (!current_user) return false;
    if (current_user.role === "admin" || isGroupAdmin) {
      return true;
    }
    return (
      repayment.from_user.id == current_user.id ||
      repayment.to_user.id == current_user.id
    );
  };

  const getUndoneMeta = (r: Repayment) =>
    [
      r.deleted_by ? `Undone by ${displayName(r.deleted_by)}` : "Undone",
      r.deleted_at
        ? new Date(r.deleted_at).toLocaleDateString("en-FI", {
            day: "numeric",
            month: "short",
          })
        : null,
      r.deleted_note?.trim() || null,
    ]
      .filter(Boolean)
      .join(" · ");

  const toggleConfirmUndoRepaymentModal = (
    open: boolean,
    repayment: Repayment | null,
  ) => {
    setSelectedRepayment(repayment ?? null);
    setShowConfirmUndoRepaymentModal(open);
  };

  return (
    <div className={styles.repaymentSection}>
      <button
        type="button"
        className={styles.toggle}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span>Payment history ({repayments.length})</span>
        <Icon
          icon={open ? "ph:caret-up" : "ph:caret-down"}
          width={16}
          height={16}
        />
      </button>
      {open && (
        <div className={styles.repaymentList}>
          {repayments &&
            repayments.length > 0 &&
            repayments.map((repayment) => (
              <div
                key={repayment.id}
                className={`${styles.repaymentItem} ${repayment.is_deleted ? styles.undone : ""}`}
              >
                <div className={styles.repaymentInfo}>
                  <div className={styles.repaymentUsernames}>
                    <span className={styles.repaymentUsername}>
                      {displayName(repayment.from_user)}
                    </span>{" "}
                    →{" "}
                    <span className={styles.repaymentUsername}>
                      {displayName(repayment.to_user)}
                    </span>
                  </div>
                  <span className={styles.repaymentMeta}>
                    {new Date(repayment.paid_at).toLocaleDateString("en-FI", {
                      day: "numeric",
                      month: "short",
                    })}
                    {repayment.note && repayment.note.trim().length > 0
                      ? ` · ${repayment.note}`
                      : ""}
                  </span>
                  {repayment.is_deleted && (
                    <span className={styles.repaymentUndoneMeta}>
                      {getUndoneMeta(repayment)}
                    </span>
                  )}
                </div>
                <div className={styles.repaymentAmountAndActions}>
                  <div
                    className={styles.repaymentActions}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {showUndoBtn(repayment) && (
                      <button
                        title="Undo this payment"
                        className={styles.undoBtn}
                        onClick={() =>
                          toggleConfirmUndoRepaymentModal(true, repayment)
                        }
                      >
                        Undo
                      </button>
                    )}
                  </div>
                  <span
                    className={`${styles.repaymentAmount} ${repayment.is_deleted ? styles.undone : ""}`}
                  >
                    €{repayment.amount.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
        </div>
      )}

      {showConfirmUndoRepaymentModal && selectedRepayment && (
        <UndoRepaymentModal
          expense_group_id={expense_group.id}
          repayment={selectedRepayment}
          onClose={() => toggleConfirmUndoRepaymentModal(false, null)}
        />
      )}
    </div>
  );
};

export default RepaymentHistory;
