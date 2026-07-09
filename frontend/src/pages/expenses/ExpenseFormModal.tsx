import { useEffect, useState } from "react";
import { Icon } from "@iconify/react";
import type {
  Category,
  Expense,
  ExpenseGroup,
  MemberExpenseShare,
  NewExpensePayload,
  UpdateExpensePayload,
} from "@/types";
import styles from "./ExpenseFormModal.module.scss";
import { Select } from "@/components/ui/Select";
import { DatePicker } from "@/components/ui/DatePicker";
import { useCreateExpense, useUpdateExpense } from "@/hooks/queries";
import { useAuthStore } from "@/stores/authStore";

interface Props {
  expense: Expense | null;
  categories: Category[];
  isEditing: boolean;
  onClose: () => void;
  expense_group?: ExpenseGroup | null;
}

const initialExpenseState = {
  name: "",
  description: "",
  value: 0,
  category_id: null,
  payee_id: null,
  expense_group_id: null,
  paid_at: null,
};

export const ExpenseFormModal = ({
  expense,
  categories,
  isEditing,
  onClose,
  expense_group,
}: Props) => {
  const { mutate: createExpense, isPending: isCreatePending } =
    useCreateExpense();
  const { mutate: updateExpense, isPending: isUpdatePending } =
    useUpdateExpense();
  const current_user = useAuthStore((s) => s.user);

  const [form, setForm] = useState<NewExpensePayload | UpdateExpensePayload>(
    initialExpenseState,
  );
  const [shares, setShares] = useState<MemberExpenseShare[]>([]);
  const [error, setError] = useState("");

  const isPending = isEditing ? isUpdatePending : isCreatePending;

  // initialize shares from expense or group members
  useEffect(() => {
    if (expense_group) {
      if (expense?.shares && expense.shares.length > 0) {
        // editing: use existing shares
        setShares(
          expense.shares.map((s) => ({ user_id: s.user_id, ratio: s.ratio })),
        );
      } else if (!isEditing) {
        // creating: use default member ratios
        setShares(
          expense_group.members.map((m) => ({
            user_id: m.user_id,
            ratio: m.default_split_ratio,
          })),
        );
      }
    }
  }, [expense_group]);

  useEffect(() => {
    if (expense) {
      setForm({
        name: expense.name,
        description: expense.description,
        value: expense.value,
        category_id: expense.category_id,
        payee_id: expense.payee_id,
        expense_group_id: expense.expense_group_id,
        paid_at: expense.paid_at,
      });
    } else {
      //Default payee to be the current user
      if (current_user) {
        setForm({ ...form, payee_id: current_user.id });
      }
    }
  }, []);

  const totalRatio = shares.reduce((sum, s) => sum + s.ratio, 0);
  const ratioValid = Math.abs(totalRatio - 1.0) < 0.001;

  const updateShareRatio = (user_id: number, value: string) => {
    const ratio = parseFloat(value) / 100;
    setShares((prev) =>
      prev.map((s) =>
        s.user_id === user_id ? { ...s, ratio: isNaN(ratio) ? 0 : ratio } : s,
      ),
    );
  };

  const addMemberToShares = (user_id: number) => {
    if (shares.find((s) => s.user_id === user_id)) return;
    setShares((prev) => [...prev, { user_id, ratio: 0 }]);
  };

  const removeMemberFromShares = (user_id: number) => {
    setShares((prev) => prev.filter((s) => s.user_id !== user_id));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // only send shares if there are any
    const sharesPayload = shares.length > 0 ? shares : undefined;

    if (sharesPayload && !ratioValid) {
      setError(
        `Share ratios must sum to 100% (currently ${Math.round(totalRatio * 100)}%)`,
      );
      return;
    }

    if (isEditing && expense) {
      updateExpense(
        {
          id: expense.id,
          data: {
            ...(form as UpdateExpensePayload),
            ...(expense_group && sharesPayload
              ? { shares: sharesPayload }
              : {}),
          },
        },
        {
          onSuccess: () => onClose(),
          onError: () =>
            setError("Failed to update expense. Please try again."),
        },
      );
    } else {
      const expensePayload = { ...form } as NewExpensePayload;
      if (expense_group) {
        expensePayload.expense_group_id = expense_group.id;
        if (sharesPayload) expensePayload.shares = sharesPayload;
      }
      createExpense(expensePayload, {
        onSuccess: () => onClose(),
        onError: () => setError("Failed to add new expense. Please try again."),
      });
    }
  };

  // members not yet in shares (for adding)
  const membersNotInShares =
    expense_group?.members.filter(
      (m) => !shares.find((s) => s.user_id === m.user_id),
    ) ?? [];

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>
            {isEditing ? "Edit expense" : "New expense"}
          </h2>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form id="expense-form" onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fields}>
            <div className={styles.field}>
              <label className={styles.label}>Name*</label>
              <input
                className={styles.input}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Amount (€)*</label>
              <input
                type="number"
                step="0.01"
                className={styles.input}
                value={form.value}
                onChange={(e) =>
                  setForm({ ...form, value: parseFloat(e.target.value) || 0 })
                }
                required
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Category</label>
              <Select
                triggerClassName={styles.dropdownTrigger}
                value={form.category_id ? form.category_id.toString() : ""}
                onChange={(v) =>
                  setForm({ ...form, category_id: v ? Number(v) : null })
                }
                options={[
                  { value: "", label: "No category" },
                  ...categories.map((c) => ({
                    value: c.id.toString(),
                    label: c.name,
                  })),
                ]}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Paid at</label>
              <DatePicker
                value={form.paid_at ?? null}
                onChange={(v) => setForm({ ...form, paid_at: v })}
              />
            </div>

            {expense_group && (
              <div className={styles.field}>
                <label className={styles.label}>Paid by</label>
                <Select
                  triggerClassName={styles.dropdownTrigger}
                  value={form.payee_id ? form.payee_id.toString() : ""}
                  onChange={(v) => setForm({ ...form, payee_id: Number(v) })}
                  options={[
                    ...expense_group.members.map((m) => ({
                      value: m.user_id.toString(),
                      label: `${m.user?.username ?? m.user_id}${m.user_id === current_user?.id ? " (you)" : ""}`,
                    })),
                    // keep a former-member payee selectable so the field isn't blank
                    ...(expense?.payee_id &&
                    !expense_group.members.some(
                      (m) => m.user_id === expense.payee_id,
                    )
                      ? [
                          {
                            value: expense.payee_id.toString(),
                            label: `${expense.payee?.username ?? `User ${expense.payee_id}`} (former member)`,
                          },
                        ]
                      : []),
                  ]}
                />
              </div>
            )}

            <div className={styles.field}>
              <label className={styles.label}>Description</label>
              <textarea
                className={styles.input}
                value={form.description ?? ""}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                rows={3}
                placeholder="Optional note"
              />
            </div>

            {expense_group && (
              <div className={styles.sharesSection}>
                <div className={styles.sharesHeader}>
                  <span className={styles.sharesTitle}>Shares</span>
                  <span
                    className={`${styles.sharesTotal} ${!ratioValid ? styles.sharesTotalInvalid : ""}`}
                  >
                    {Math.round(totalRatio * 100)}%
                  </span>
                </div>

                <div className={styles.sharesList}>
                  {shares.map((share) => {
                    const member = expense_group.members.find(
                      (m) => m.user_id === share.user_id,
                    );
                    const isCurrentUser = share.user_id === current_user?.id;

                    return (
                      <div key={share.user_id} className={styles.shareRow}>
                        <div className={styles.shareAvatar}>
                          {(member?.user?.firstname ??
                            member?.user?.username ??
                            "?")[0].toUpperCase()}
                        </div>
                        <div className={styles.shareInfo}>
                          <span className={styles.shareName}>
                            {member?.user?.firstname || member?.user?.lastname
                              ? `${member?.user?.firstname ?? ""} ${member?.user?.lastname ?? ""}`.trim()
                              : (member?.user?.username ??
                                `User ${share.user_id}`)}
                            {isCurrentUser ? " (you)" : ""}
                          </span>
                          {(member?.user?.firstname ||
                            member?.user?.lastname) && (
                            <span className={styles.shareUsername}>
                              @{member?.user?.username}
                            </span>
                          )}
                        </div>
                        <div className={styles.shareInputWrap}>
                          <input
                            type="number"
                            min="0"
                            max="100"
                            step="0.1"
                            className={styles.shareInput}
                            value={Math.round(share.ratio * 1000) / 10}
                            onChange={(e) =>
                              updateShareRatio(share.user_id, e.target.value)
                            }
                          />
                          <span className={styles.shareSuffix}>%</span>
                        </div>
                        <button
                          type="button"
                          className={styles.shareRemoveBtn}
                          onClick={() => removeMemberFromShares(share.user_id)}
                          title="Remove"
                        >
                          <Icon icon="ph:x" width={14} height={14} />
                        </button>
                      </div>
                    );
                  })}
                </div>

                {membersNotInShares.length > 0 && (
                  <div className={styles.addShareRow}>
                    <Select
                      triggerClassName={styles.dropdownTrigger}
                      value=""
                      onChange={(v) => addMemberToShares(Number(v))}
                      placeholder="+ Add member"
                      options={membersNotInShares.map((m) => ({
                        value: m.user_id.toString(),
                        label: `${m.user?.username ?? m.user_id}${m.user_id === current_user?.id ? " (you)" : ""}`,
                      }))}
                    />
                  </div>
                )}

                {shares.length > 0 && !ratioValid && (
                  <p className={styles.sharesHint}>
                    Shares must add up to 100%.{" "}
                    <button
                      type="button"
                      className={styles.distributeBtn}
                      onClick={() => {
                        const equal =
                          Math.round((1 / shares.length) * 10000) / 10000;
                        setShares((prev) =>
                          prev.map((s, i) => ({
                            ...s,
                            ratio:
                              i === shares.length - 1
                                ? Math.round(
                                    (1 - equal * (shares.length - 1)) * 10000,
                                  ) / 10000
                                : equal,
                          })),
                        );
                      }}
                    >
                      Distribute equally
                    </button>
                  </p>
                )}
              </div>
            )}
          </div>

          {error && (
            <div className={styles.errorBanner}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {error}
            </div>
          )}

          <div className={styles.formActions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelBtn}
            >
              {isEditing ? "Cancel" : "Close"}
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isPending}
            >
              {isEditing ? "Save changes" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
