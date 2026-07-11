import { useEffect, useState } from "react";
import { Icon } from "@iconify/react";
import {
  useExpensesPaginated,
  useUpdateExpense,
  useCategories,
} from "@/hooks/queries";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import type { Expense, ExpenseStatusFilter } from "@/types";
import styles from "./ExpensesPage.module.scss";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { Select } from "@/components/ui/Select";
import { Pagination } from "@/components/ui/Pagination";
import { CategoryBreakdownCard } from "@/components/CategoryBreakdownCard";
import { ExpenseFormModal } from "./ExpenseFormModal";
import { ExpenseDetailsModal } from "./ExpenseDetailsModal";
import {
  EXPENSE_SORT_OPTIONS,
  DEFAULT_EXPENSE_SORT,
  parseExpenseSort,
  type ExpenseSortValue,
} from "./expenseSortOptions";

export const ExpensesPage = () => {
  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(
    null,
  );

  const [status, setStatus] = useState<ExpenseStatusFilter>("active");
  const [searchInput, setSearchInput] = useState("");
  // "" = all categories, "none" = no category, else a category id
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sort, setSort] = useState<ExpenseSortValue>(DEFAULT_EXPENSE_SORT);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [showExpenseFormModal, setShowExpenseFormModal] = useState(false);
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);
  const [showConfirmDeleteModal, setShowConfirmDeleteModal] = useState(false);
  const [error, setError] = useState("");

  const debouncedSearch = useDebouncedValue(searchInput);
  const { sort_by, sort_dir } = parseExpenseSort(sort);

  useEffect(() => {
    setPage(1);
  }, [status, debouncedSearch, categoryFilter, sort, pageSize]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const { data, isLoading } = useExpensesPaginated({
    status,
    search_kw: debouncedSearch || undefined,
    category_id:
      categoryFilter && categoryFilter !== "none"
        ? Number(categoryFilter)
        : undefined,
    no_category: categoryFilter === "none" ? true : undefined,
    sort_by,
    sort_dir,
    page,
    page_size: pageSize,
  });
  const { data: categories = [] } = useCategories();
  const { mutate: updateExpense } = useUpdateExpense();

  const expenses = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalValue = data?.total_value ?? 0;
  const totalPages = data?.total_pages ?? 1;

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

  const hasFilters = debouncedSearch.trim() !== "" || categoryFilter !== "";

  const clearFilters = () => {
    setSearchInput("");
    setCategoryFilter("");
  };

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

      <CategoryBreakdownCard />

      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {(["all", "active", "deleted"] as ExpenseStatusFilter[]).map((f) => (
            <button
              key={f}
              className={`${styles.filterBtn} ${status === f ? styles.filterActive : ""}`}
              onClick={() => setStatus(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <div className={styles.totalBadge}>
          Total: <strong>€{totalValue.toFixed(2)}</strong>
        </div>
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
        <div className={styles.loading}>
          <Icon
            icon="ph:circle-notch"
            width={24}
            height={24}
            className={styles.spin}
          />
        </div>
      ) : expenses.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:receipt" width={40} height={40} />
          {hasFilters ? (
            <>
              <p>No expenses match your search</p>
              <button className={styles.emptyAction} onClick={clearFilters}>
                Clear filters
              </button>
            </>
          ) : status !== "active" ? (
            <p>No expenses found</p>
          ) : (
            <>
              <p>No expenses found</p>
              <button
                className={styles.emptyAction}
                onClick={() => toggleExpenseFormModal(true)}
              >
                Add your first expense
              </button>
            </>
          )}
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

      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        onChange={setPage}
        pageSize={pageSize}
        onPageSizeChange={setPageSize}
      />

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
