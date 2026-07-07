import { useEffect, useState } from "react";
import styles from "./ExpensesTab.module.scss";
import { useCategories, useUpdateExpense } from "@/hooks/queries";
import { ExpenseFormModal } from "@/pages/expenses/ExpenseFormModal";
import { ExpenseDetailsModal } from "@/pages/expenses/ExpenseDetailsModal";
import { Expense, ExpenseGroup } from "@/types";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

type Props = {
  expense_group: ExpenseGroup;
  expenses: Expense[];
};

const ExpensesTab = ({ expense_group, expenses }: Props) => {
  const { data: categories = [] } = useCategories({
    expense_group_id: expense_group.id,
  });
  const { mutate: updateExpense } = useUpdateExpense();
  const current_user = useAuthStore((s) => s.user);

  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(
    null,
  );
  const [showExpenseFormModal, setShowExpenseFormModal] = useState(false);
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);
  const [showConfirmDeleteExpenseModal, setShowConfirmDeleteExpenseModal] =
    useState(false);
  const [expenseFilter, setExpenseFilter] = useState<
    "active" | "deleted" | "all"
  >("active");
  const [error, setError] = useState("");

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

  const filteredExpenses = expenses.filter((e) => {
    if (expenseFilter === "active") return !e.is_deleted;
    if (expenseFilter === "deleted") return e.is_deleted;
    return true;
  });

  const toggleExpenseFormModal = (open: boolean, expense?: Expense) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowExpenseFormModal(open);
  };

  const toggleExpenseDetailsModal = (open: boolean, expense?: Expense) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowExpenseDetailsModal(open);
  };

  const toggleConfirmDeleteExpenseModal = (
    open: boolean,
    expense?: Expense,
  ) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowConfirmDeleteExpenseModal(open);
  };

  const handleConfirmDelete = () => {
    if (selectedExpense) {
      setError("");
      toggleConfirmDeleteExpenseModal(false);
      updateExpense(
        {
          id: selectedExpense.id,
          data: { is_deleted: !selectedExpense.is_deleted },
        },
        {
          onError: () => {
            setError(
              selectedExpense.is_deleted
                ? "Failed to restore expense. Please try again."
                : "Failed to delete expense. Please try again.",
            );
          },
        },
      );
    }
  };

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        {/* <h2 className={styles.sectionTitle}>Expenses</h2> */}
        {/* <div className={styles.sectionRight}> */}
        <div className={styles.filters}>
          {(["active", "all", "deleted"] as const).map((f) => (
            <button
              key={f}
              className={`${styles.filterBtn} ${expenseFilter === f ? styles.filterActive : ""}`}
              onClick={() => setExpenseFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <button
          className={styles.addBtn}
          onClick={() => toggleExpenseFormModal(true)}
        >
          <Icon icon="ph:plus" width={16} height={16} />
          Add
        </button>
        {/* </div> */}
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <Icon icon="ph:warning-circle" width={16} height={16} />
          {error}
        </div>
      )}

      {filteredExpenses.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:receipt" width={36} height={36} />
          <p>No expenses found</p>
        </div>
      ) : (
        <div className={styles.list}>
          {filteredExpenses.map((expense) => (
            <div
              key={expense.id}
              className={`${styles.item} ${expense.is_deleted ? styles.itemDeleted : ""}`}
              onClick={() => toggleExpenseDetailsModal(true, expense)}
            >
              <div className={styles.itemIcon}>
                <Icon icon="ph:receipt" width={17} height={17} />
              </div>
              <div className={styles.itemInfo}>
                <span className={styles.itemName}>{expense.name}</span>
                <span className={styles.itemMeta}>
                  Paid by{" "}
                  <strong>
                    {expense_group.members.find(
                      (m) => m.user_id === expense.payee_id,
                    )?.user?.username ?? "unknown"}
                    {expense.payee_id === current_user?.id ? " (you)" : ""}
                  </strong>
                  {" · "}
                  {new Date(expense.created_at).toLocaleDateString("en-FI", {
                    day: "numeric",
                    month: "short",
                  })}
                </span>
              </div>
              <span className={styles.itemValue}>
                €{expense.value.toFixed(2)}
              </span>
              <div
                className={styles.itemActions}
                onClick={(e) => e.stopPropagation()}
              >
                {!expense.is_deleted && (
                  <button
                    className={styles.actionBtn}
                    onClick={() => toggleExpenseFormModal(true, expense)}
                  >
                    <Icon icon="ph:pencil-simple" width={15} height={15} />
                  </button>
                )}
                <button
                  className={`${styles.actionBtn} ${expense.is_deleted ? styles.actionRestore : styles.actionDelete}`}
                  onClick={() => toggleConfirmDeleteExpenseModal(true, expense)}
                >
                  <Icon
                    icon={
                      expense.is_deleted
                        ? "ph:arrow-counter-clockwise"
                        : "ph:trash"
                    }
                    width={15}
                    height={15}
                  />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showExpenseFormModal && (
        <ExpenseFormModal
          expense={selectedExpense}
          expense_group={expense_group}
          categories={categories}
          isEditing={!!selectedExpense}
          onClose={() => toggleExpenseFormModal(false)}
        />
      )}

      {showExpenseDetailsModal && selectedExpense && (
        <ExpenseDetailsModal
          expense={selectedExpense}
          categories={categories}
          expense_group={expense_group}
          onClose={() => toggleExpenseDetailsModal(false)}
        />
      )}

      {showConfirmDeleteExpenseModal && selectedExpense && (
        <ConfirmModal
          title={
            selectedExpense.is_deleted ? "Restore expense?" : "Delete expense?"
          }
          message={`"${selectedExpense.name}" will be ${selectedExpense.is_deleted ? "restored" : "moved to Deleted"}.`}
          confirmLabel={selectedExpense.is_deleted ? "Restore" : "Delete"}
          danger={!selectedExpense.is_deleted}
          onConfirm={handleConfirmDelete}
          onCancel={() => toggleConfirmDeleteExpenseModal(false)}
        />
      )}
    </div>
  );
};

export default ExpensesTab;
