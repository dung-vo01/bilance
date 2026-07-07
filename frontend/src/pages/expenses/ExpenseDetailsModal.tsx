import { useState } from "react";
import { Icon } from "@iconify/react";
import type { Category, Expense, ExpenseGroup } from "@/types";
import styles from "./ExpenseDetailsModal.module.scss";
import { ExpenseFormModal } from "./ExpenseFormModal";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { useUpdateExpense } from "@/hooks/queries";
import { useAuthStore } from "@/stores/authStore";

interface Props {
  expense: Expense;
  categories: Category[];
  onClose: () => void;
  expense_group?: ExpenseGroup | null;
}

export const ExpenseDetailsModal = ({
  expense,
  categories,
  onClose,
  expense_group,
}: Props) => {
  const current_user = useAuthStore((s) => s.user);
  const { mutate: updateExpense } = useUpdateExpense();

  const [showExpenseFormModal, setShowExpenseFormModal] = useState(false);
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);
  const [error, setError] = useState("");

  const category = categories.find((c) => c.id === expense.category_id);

  const toggleExpenseFormModal = (open: boolean) => {
    setShowExpenseFormModal(open);
  };

  const toggleConfirmDeleteModal = (open: boolean) => {
    setShowConfirmDeleteModal(open);
  };

  const handleConfirmDelete = () => {
    setError("");
    toggleConfirmDeleteModal(false);
    updateExpense(
      {
        id: expense.id,
        data: { is_deleted: !expense.is_deleted },
      },
      {
        onError: () => {
          setError(
            expense.is_deleted
              ? "Failed to restore expense. Please try again."
              : "Failed to delete expense. Please try again.",
          );
        },
      },
    );
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.titleRow}>
            <h2 className={styles.modalTitle}>Expense details</h2>
            {expense.is_deleted && (
              <span className={styles.deletedBadge}>Deleted</span>
            )}
          </div>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <div className={styles.detailGrid}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Name</span>
            <span className={styles.detailValue}>{expense.name}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Amount</span>
            <span className={`${styles.detailValue} ${styles.amount}`}>
              €{expense.value.toFixed(2)}
            </span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Category</span>
            <span className={styles.detailValue}>{category?.name ?? "—"}</span>
          </div>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Date paid</span>
            <span className={styles.detailValue}>
              {expense.paid_at
                ? new Date(expense.paid_at).toLocaleDateString("en-FI", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })
                : "Unknown"}
            </span>
          </div>
          {expense_group && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Paid by</span>
              <span className={styles.detailValue}>
                {expense_group.members.find(
                  (m) => m.user_id === expense.payee_id,
                )?.user?.username ?? "unknown"}
                {expense.payee_id === current_user?.id ? " (you)" : ""}
              </span>
            </div>
          )}
          {expense.description && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Note</span>
              <span className={styles.detailValue}>{expense.description}</span>
            </div>
          )}
        </div>

        {expense.shares && expense.shares.length > 0 && (
          <div className={styles.sharesSection}>
            <span className={styles.sharesTitle}>Shares</span>
            <div className={styles.sharesList}>
              {expense.shares.map((share) => {
                const member = expense_group?.members.find(
                  (m) => m.user_id === share.user_id,
                );
                const username =
                  member?.user?.username ?? `User ${share.user_id}`;
                const fullName =
                  member?.user?.firstname || member?.user?.lastname
                    ? `${member?.user?.firstname ?? ""} ${member?.user?.lastname ?? ""}`.trim()
                    : null;
                const isCurrentUser = share.user_id === current_user?.id;

                return (
                  <div key={share.user_id} className={styles.shareRow}>
                    <div className={styles.shareAvatar}>
                      {(fullName ?? username)[0].toUpperCase()}
                    </div>
                    <div className={styles.shareInfo}>
                      <span className={styles.shareName}>
                        {fullName ?? username}
                        {isCurrentUser ? " (you)" : ""}
                      </span>
                      {fullName && (
                        <span className={styles.shareUsername}>
                          @{username}
                        </span>
                      )}
                    </div>
                    <div className={styles.shareAmounts}>
                      <span className={styles.shareAmount}>
                        €{share.amount.toFixed(2)}
                      </span>
                      <span className={styles.shareRatio}>
                        {Math.round(share.ratio * 100)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {error && (
          <div className={styles.errorBanner}>
            <Icon icon="ph:warning-circle" width={16} height={16} />
            {error}
          </div>
        )}

        <div className={styles.modalActions}>
          {!expense.is_deleted && (
            <button
              className={styles.editBtn}
              onClick={() => toggleExpenseFormModal(true)}
            >
              <Icon icon="ph:pencil-simple" width={16} height={16} />
              Edit
            </button>
          )}
          <button
            className={`${styles.deleteBtn} ${expense.is_deleted ? styles.restoreBtn : ""}`}
            onClick={() => toggleConfirmDeleteModal(true)}
          >
            <Icon
              icon={
                expense.is_deleted ? "ph:arrow-counter-clockwise" : "ph:trash"
              }
              width={16}
              height={16}
            />
            {expense.is_deleted ? "Restore" : "Delete"}
          </button>
        </div>
      </div>

      {showExpenseFormModal && (
        <ExpenseFormModal
          expense={expense}
          categories={categories}
          isEditing
          expense_group={expense_group}
          onClose={() => toggleExpenseFormModal(false)}
        />
      )}

      {showConfirmDeleteModal && (
        <ConfirmModal
          title={expense.is_deleted ? "Restore expense?" : "Delete expense?"}
          message={`"${expense.name}" will be ${expense.is_deleted ? "restored" : "moved to Deleted"}.`}
          confirmLabel={expense.is_deleted ? "Restore" : "Delete"}
          danger={!expense.is_deleted}
          onConfirm={handleConfirmDelete}
          onCancel={() => toggleConfirmDeleteModal(false)}
        />
      )}
    </div>
  );
};
