import { useCreateExpenseGroup, useUpdateExpenseGroup } from "@/hooks/queries";
import {
  ExpenseGroup,
  NewExpenseGroupPayload,
  UpdateExpenseGroupPayload,
} from "@/types";
import { useEffect, useState } from "react";
import styles from "./ExpenseGroupFormModal.module.scss";
import { Icon } from "@iconify/react";

interface Props {
  expenseGroup: ExpenseGroup | null;
  isEditing: boolean;
  onClose: () => void;
}

const initialExpenseGroupState = {
  name: "",
  description: "",
};

const ExpenseGroupFormModal = ({ expenseGroup, isEditing, onClose }: Props) => {
  const { mutate: createExpenseGroup, isPending: isCreatePending } =
    useCreateExpenseGroup();

  const { mutate: updateExpenseGroup, isPending: isUpdatePending } =
    useUpdateExpenseGroup();

  const isPending = isEditing ? isUpdatePending : isCreatePending;

  const [form, setForm] = useState<
    NewExpenseGroupPayload | UpdateExpenseGroupPayload
  >(initialExpenseGroupState);
  const [error, setError] = useState("");

  useEffect(() => {
    if (expenseGroup) {
      setForm({
        name: expenseGroup.name,
        description: expenseGroup.description,
      });
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (isEditing && expenseGroup) {
      updateExpenseGroup(
        { groupId: expenseGroup.id, data: form as UpdateExpenseGroupPayload },
        {
          onSuccess: () => {
            onClose();
          },
          onError: () => setError("Failed to update group. Please try again."),
        },
      );
    } else {
      createExpenseGroup(form as NewExpenseGroupPayload, {
        onSuccess: () => {
          onClose();
        },
        onError: () => setError("Failed to add new group. Please try again."),
      });
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.titleRow}>
            <h2 className={styles.modalTitle}>
              {isEditing ? "Edit group" : "New group"}
            </h2>
            {isPending && (
              <Icon
                icon="ph:circle-notch"
                width={16}
                height={16}
                className={styles.spin}
              />
            )}
          </div>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fields}>
            <div className={styles.field}>
              <label className={styles.label}>Group name*</label>
              <input
                className={styles.input}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Groceries, rent, trip..."
                required
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Description</label>
              <textarea
                className={styles.input}
                value={form.description ? form.description : ""}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                rows={3}
                placeholder="Optional"
              />
            </div>
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
              {isEditing ? "Save changes" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ExpenseGroupFormModal;
