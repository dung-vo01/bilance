import { useState, useMemo, useEffect } from "react";
import { Icon } from "@iconify/react";
import { useExpenses, useUpdateExpense, useCategories } from "@/hooks/queries";
import type { Expense } from "@/types";
import styles from "./ExpensesPage.module.scss";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { ExpenseFormModal } from "./ExpenseFormModal";
import { ExpenseDetailsModal } from "./ExpenseDetailsModal";

type Filter = "all" | "active" | "deleted";

export const ExpensesPage = () => {
  const { data: expenses = [], isLoading } = useExpenses();
  const { data: categories = [] } = useCategories();
  const { mutate: updateExpense } = useUpdateExpense();
  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(
    null,
  );

  const [filter, setFilter] = useState<Filter>("active");
  const [showExpenseFormModal, setShowExpenseFormModal] = useState(false);
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

  const filtered = useMemo(() => {
    return expenses.filter((e) => {
      if (e.expense_group_id) return false;
      if (filter === "active") return !e.is_deleted;
      if (filter === "deleted") return e.is_deleted;
      return true;
    });
  }, [expenses, filter]);

  const total = useMemo(
    () =>
      filtered
        .filter((e) => !e.is_deleted)
        .reduce((sum, e) => sum + e.value, 0),
    [filtered],
  );

  const toggleExpenseDetailsModal = (open: boolean, expense?: Expense) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowExpenseDetailsModal(open);
  };

  const toggleExpenseFormModal = (open: boolean, expense?: Expense) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowExpenseFormModal(open);
  };

  const toggleConfirmDeleteModal = (open: boolean, expense?: Expense) => {
    setSelectedExpenseId(expense ? expense.id : null);
    setShowConfirmDeleteModal(open);
  };

  const handleConfirmDelete = () => {
    if (selectedExpense) {
      setError("");
      toggleConfirmDeleteModal(false);
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
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Personal expenses</h1>
          <p className={styles.subtitle}>Track your own spending</p>
        </div>
        <button
          className={styles.addBtn}
          onClick={() => toggleExpenseFormModal(true)}
        >
          <Icon icon="ph:plus" width={16} height={16} />
          Add expense
        </button>
      </div>

      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {(["all", "active", "deleted"] as Filter[]).map((f) => (
            <button
              key={f}
              className={`${styles.filterBtn} ${filter === f ? styles.filterActive : ""}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <div className={styles.totalBadge}>
          Total: <strong>€{total.toFixed(2)}</strong>
        </div>
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <Icon icon="ph:warning-circle" width={16} height={16} />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className={styles.loading}>
          <Icon
            icon="ph:circle-notch"
            width={24}
            height={24}
            className={styles.spin}
          />
        </div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:receipt" width={40} height={40} />
          <p>No expenses found</p>
          <button
            className={styles.emptyAction}
            onClick={() => toggleExpenseFormModal(true)}
          >
            Add your first expense
          </button>
        </div>
      ) : (
        <div className={styles.list}>
          {filtered.map((expense) => (
            <div
              key={expense.id}
              className={`${styles.item} ${expense.is_deleted ? styles.itemDeleted : ""}`}
              onClick={() => toggleExpenseDetailsModal(true, expense)}
            >
              <div className={styles.itemIcon}>
                <Icon icon="ph:receipt" width={18} height={18} />
              </div>

              <div className={styles.itemInfo}>
                <span className={styles.itemName}>{expense.name}</span>
                {expense.description && (
                  <span className={styles.itemDesc}>{expense.description}</span>
                )}
                <span className={styles.itemMeta}>
                  {expense.category_id
                    ? categories.find((c) => c.id === expense.category_id)?.name
                    : "No category"}
                  {expense.paid_at
                    ? " - " +
                      new Date(expense.paid_at).toLocaleDateString("en-FI", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })
                    : ""}
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
                    title="Edit"
                  >
                    <Icon icon="ph:pencil-simple" width={16} height={16} />
                  </button>
                )}
                <button
                  className={`${styles.actionBtn} ${expense.is_deleted ? styles.actionRestore : styles.actionDelete}`}
                  onClick={() => {
                    toggleConfirmDeleteModal(true, expense);
                  }}
                >
                  <Icon
                    icon={
                      expense.is_deleted
                        ? "ph:arrow-counter-clockwise"
                        : "ph:trash"
                    }
                    width={16}
                    height={16}
                  />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showExpenseDetailsModal && selectedExpense && (
        <ExpenseDetailsModal
          expense={selectedExpense}
          categories={categories}
          onClose={() => toggleExpenseDetailsModal(false)}
        />
      )}

      {showExpenseFormModal && (
        <ExpenseFormModal
          expense={selectedExpense}
          categories={categories}
          isEditing={!!selectedExpense}
          onClose={() => toggleExpenseFormModal(false)}
        />
      )}

      {showConfirmDeleteModal && selectedExpense && (
        <ConfirmModal
          title={
            selectedExpense.is_deleted ? "Restore expense?" : "Delete expense?"
          }
          message={`"${selectedExpense.name}" will be ${selectedExpense.is_deleted ? "restored" : "moved to Deleted"}.`}
          confirmLabel={selectedExpense.is_deleted ? "Restore" : "Delete"}
          danger={!selectedExpense.is_deleted}
          onConfirm={handleConfirmDelete}
          onCancel={() => toggleConfirmDeleteModal(false)}
        />
      )}
    </div>
  );
};
