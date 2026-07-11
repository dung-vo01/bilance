import { useEffect, useState } from "react";
import styles from "./ExpensesTab.module.scss";
import {
  useCategories,
  useExpensePayees,
  useExpensesPaginated,
  useUpdateExpense,
} from "@/hooks/queries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { ExpenseFormModal } from "@/pages/expenses/ExpenseFormModal";
import { ExpenseDetailsModal } from "@/pages/expenses/ExpenseDetailsModal";
import {
  EXPENSE_SORT_OPTIONS,
  DEFAULT_EXPENSE_SORT,
  parseExpenseSort,
  type ExpenseSortValue,
} from "@/pages/expenses/expenseSortOptions";
import { Expense, ExpenseGroup, ExpenseStatusFilter } from "@/types";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { Select } from "@/components/ui/Select";
import { Pagination } from "@/components/ui/Pagination";
import { CategoryBreakdownCard } from "@/components/CategoryBreakdownCard";

type Props = {
  expense_group: ExpenseGroup;
};

const ExpensesTab = ({ expense_group }: Props) => {
  const { data: categories = [] } = useCategories({
    expense_group_id: expense_group.id,
  });
  const { data: payees = [] } = useExpensePayees(expense_group.id);
  const { mutate: updateExpense } = useUpdateExpense();
  const current_user = useAuthStore((s) => s.user);

  const memberIds = new Set(expense_group.members.map((m) => m.user_id));
  // payees no longer in the group (left/removed) but still filterable
  const formerPayees = payees.filter((p) => !memberIds.has(p.id));

  const getPayeeDisplay = (expense: Expense) => {
    const username =
      expense.payee?.username ??
      expense_group.members.find((m) => m.user_id === expense.payee_id)?.user
        ?.username ??
      "unknown";
    if (expense.payee_id === current_user?.id) return `${username} (you)`;
    if (!memberIds.has(expense.payee_id)) return `${username} (former member)`;
    return username;
  };

  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(
    null,
  );
  const [showExpenseFormModal, setShowExpenseFormModal] = useState(false);
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);
  const [showConfirmDeleteExpenseModal, setShowConfirmDeleteExpenseModal] =
    useState(false);
  const [expenseFilter, setExpenseFilter] =
    useState<ExpenseStatusFilter>("active");
  const [searchInput, setSearchInput] = useState("");
  // "" = all categories, "none" = no category, else a category id
  const [categoryFilter, setCategoryFilter] = useState("");
  const [payeeId, setPayeeId] = useState<number | null>(null);
  const [sort, setSort] = useState<ExpenseSortValue>(DEFAULT_EXPENSE_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [error, setError] = useState("");

  const debouncedSearch = useDebouncedValue(searchInput);
  const { sort_by, sort_dir } = parseExpenseSort(sort);

  useEffect(() => {
    setPage(1);
  }, [expenseFilter, debouncedSearch, categoryFilter, payeeId, sort, pageSize]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const { data, isLoading } = useExpensesPaginated({
    expense_group_id: expense_group.id,
    status: expenseFilter,
    search_kw: debouncedSearch || undefined,
    category_id:
      categoryFilter && categoryFilter !== "none"
        ? Number(categoryFilter)
        : undefined,
    no_category: categoryFilter === "none" ? true : undefined,
    payee_id: payeeId ?? undefined,
    sort_by,
    sort_dir,
    page,
    page_size: pageSize,
  });

  const expenses = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

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
      <CategoryBreakdownCard expenseGroupId={expense_group.id} />

      <div className={styles.sectionHeader}>
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
      </div>

      <div className={styles.controlsRow}>
        <div className={styles.searchBar}>
          <Icon
            icon="ph:magnifying-glass"
            width={16}
            height={16}
            className={styles.searchIcon}
          />
          <input
            className={styles.searchInput}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search name or description..."
          />
        </div>

        <Select
          wrapperClassName={styles.filterSelect}
          triggerClassName={styles.dropdownTrigger}
          value={categoryFilter}
          onChange={setCategoryFilter}
          placeholder="All categories"
          options={[
            { value: "", label: "All categories" },
            { value: "none", label: "No category" },
            ...categories.map((c) => ({
              value: c.id.toString(),
              label: c.name,
            })),
          ]}
        />

        <Select
          wrapperClassName={styles.filterSelect}
          triggerClassName={styles.dropdownTrigger}
          value={payeeId ? payeeId.toString() : ""}
          onChange={(v) => setPayeeId(v ? Number(v) : null)}
          placeholder="Paid by anyone"
          options={[
            { value: "", label: "Paid by anyone" },
            ...expense_group.members.map((m) => ({
              value: m.user_id.toString(),
              label: `${m.user?.username ?? m.user_id}${m.user_id === current_user?.id ? " (you)" : ""}`,
            })),
            ...formerPayees.map((p) => ({
              value: p.id.toString(),
              label: `${p.username} (former member)`,
            })),
          ]}
        />

        <Select
          wrapperClassName={styles.filterSelect}
          triggerClassName={styles.dropdownTrigger}
          value={sort}
          onChange={(v) => setSort(v as ExpenseSortValue)}
          options={EXPENSE_SORT_OPTIONS}
        />
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <Icon icon="ph:warning-circle" width={16} height={16} />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className={styles.empty}>
          <Icon
            icon="ph:circle-notch"
            width={24}
            height={24}
            className={styles.spin}
          />
        </div>
      ) : expenses.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:receipt" width={36} height={36} />
          <p>No expenses found</p>
        </div>
      ) : (
        <div className={styles.list}>
          {expenses.map((expense) => (
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
                  Paid by <strong>{getPayeeDisplay(expense)}</strong>
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

      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        onChange={setPage}
        pageSize={pageSize}
        onPageSizeChange={setPageSize}
      />

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
