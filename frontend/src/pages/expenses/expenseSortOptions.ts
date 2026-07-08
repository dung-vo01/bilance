import type { ExpenseSortBy, SortDir } from "@/types";

export type ExpenseSortValue = `${ExpenseSortBy}_${SortDir}`;

export const EXPENSE_SORT_OPTIONS: {
  value: ExpenseSortValue;
  label: string;
}[] = [
  { value: "paid_at_desc", label: "Date paid (newest)" },
  { value: "paid_at_asc", label: "Date paid (oldest)" },
  { value: "created_at_desc", label: "Date created (newest)" },
  { value: "created_at_asc", label: "Date created (oldest)" },
  { value: "name_asc", label: "Name (A-Z)" },
  { value: "name_desc", label: "Name (Z-A)" },
  { value: "value_desc", label: "Amount (high to low)" },
  { value: "value_asc", label: "Amount (low to high)" },
];

export const DEFAULT_EXPENSE_SORT: ExpenseSortValue = "paid_at_desc";

export const parseExpenseSort = (
  value: ExpenseSortValue,
): { sort_by: ExpenseSortBy; sort_dir: SortDir } => {
  const sepIndex = value.lastIndexOf("_");
  return {
    sort_by: value.slice(0, sepIndex) as ExpenseSortBy,
    sort_dir: value.slice(sepIndex + 1) as SortDir,
  };
};
