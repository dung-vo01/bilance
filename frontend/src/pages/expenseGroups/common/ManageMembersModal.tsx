import { useState } from "react";
import { Icon } from "@iconify/react";
import type { ExpenseGroup, ExpenseGroupMember } from "@/types";
import { useRemoveMembers, useBulkUpdateGroupMembers } from "@/hooks/queries";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { Select } from "@/components/ui/Select";
import styles from "./ManageMembersModal.module.scss";
import { useAuthStore } from "@/stores/authStore";

type Props = {
  expense_group: ExpenseGroup;
  onClose: () => void;
};

type MemberEdit = {
  default_split_ratio: string;
  role: "admin" | "member";
};

const ManageMembersModal = ({ expense_group, onClose }: Props) => {
  const current_user = useAuthStore((s) => s.user);
  const { mutate: bulkUpdateMembers, isPending: isUpdating } =
    useBulkUpdateGroupMembers(expense_group.id);
  const { mutate: removeMembers } = useRemoveMembers(expense_group.id);

  const [edits, setEdits] = useState<Record<number, MemberEdit>>(() => {
    const initial: Record<number, MemberEdit> = {};
    expense_group.members.forEach((m) => {
      initial[m.user_id] = {
        default_split_ratio: String(
          Math.round(m.default_split_ratio * 100 * 100) / 100,
        ),
        role: m.role as "admin" | "member",
      };
    });
    return initial;
  });

  const [confirmRemove, setConfirmRemove] = useState<ExpenseGroupMember | null>(
    null,
  );
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const totalRatio = Object.values(edits).reduce(
    (sum, e) => sum + (parseFloat(e.default_split_ratio) || 0),
    0,
  );
  const roundedTotal = Math.round(totalRatio * 100) / 100;
  const ratioStatus =
    roundedTotal === 100 ? "exact" : roundedTotal < 100 ? "under" : "over";
  const ratioValid = ratioStatus !== "over";
  const isAdmin = expense_group.members.some(
    (m) => m.user_id === current_user?.id && m.role === "admin",
  );

  // dynamic admin count from edits for UI logic
  const editedAdminCount = Object.values(edits).filter(
    (e) => e.role === "admin",
  ).length;

  const canEditRole = (member: ExpenseGroupMember) => {
    if (!isAdmin) return false; // never had admin — can never edit roles

    if (member.user_id === current_user?.id) {
      // can always change own role back as long as another admin exists
      return editedAdminCount > 1 || edits[member.user_id]?.role === "member";
    }

    if (edits[member.user_id]?.role === "admin") {
      return editedAdminCount > 1;
    }

    return true;
  };

  const updateEdit = (
    user_id: number,
    field: keyof MemberEdit,
    value: string,
  ) => {
    setEdits((prev) => ({
      ...prev,
      [user_id]: { ...prev[user_id], [field]: value },
    }));
  };

  const distributeEqually = () => {
    if (isAdmin) {
      const count = expense_group.members.length;
      const equal = Math.round((100 / count) * 100) / 100;
      const last = Math.round((100 - equal * (count - 1)) * 100) / 100;
      const updated: Record<number, MemberEdit> = {};
      expense_group.members.forEach((m, i) => {
        updated[m.user_id] = {
          ...edits[m.user_id],
          default_split_ratio: i === count - 1 ? String(last) : String(equal),
        };
      });
      setEdits(updated);
    } else {
      setError("Must be an admin.");
    }
  };

  const handleSave = () => {
    if (!ratioValid) {
      setError(`Total must be 100% (currently ${roundedTotal}%)`);
      return;
    }

    const newAdminCount = Object.values(edits).filter(
      (e) => e.role === "admin",
    ).length;
    if (newAdminCount === 0) {
      setError("There must be at least one admin.");
      return;
    }

    setError("");

    const members = expense_group.members.map((m) => {
      const edit = edits[m.user_id];
      const payload: {
        user_id: number;
        default_split_ratio?: number;
        role?: string;
      } = {
        user_id: m.user_id,
      };

      const newRatio = parseFloat(edit.default_split_ratio) / 100;
      if (Math.abs(newRatio - m.default_split_ratio) > 0.0001) {
        payload.default_split_ratio = newRatio;
      }

      if (edit.role !== m.role) {
        payload.role = edit.role;
      }

      return payload;
    });

    bulkUpdateMembers(members, {
      onSuccess: () => {
        setSuccess("Members updated successfully.");
        // setTimeout(() => onClose(), 1000);
      },
      onError: () => setError("Failed to update members. Please try again."),
    });
  };

  const handleRemove = (member: ExpenseGroupMember) => {
    removeMembers([member.user_id], {
      onSuccess: () => {
        setConfirmRemove(null);
        const updated = { ...edits };
        delete updated[member.user_id];
        setEdits(updated);
      },
      onError: () => setError("Failed to remove member. Please try again."),
    });
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>
            {isAdmin ? "Manage members" : "Adjust your split"}
          </h2>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <div className={styles.ratioBar}>
          <div className={styles.ratioBarLeft}>
            <span className={styles.ratioTotal}>Total: {roundedTotal}%</span>

            <span
              className={`${styles.ratioHint} ${styles[`ratioHint_${ratioStatus}`]}`}
            >
              ({ratioStatus === "exact" && "Total is 100% ✓"}
              {ratioStatus === "under" &&
                `${Math.round((100 - roundedTotal) * 100) / 100}% remaining`}
              {ratioStatus === "over" &&
                `Exceeds by ${Math.round((roundedTotal - 100) * 100) / 100}%`}
              )
            </span>
          </div>
          {isAdmin && (
            <button
              className={styles.distributeBtn}
              onClick={distributeEqually}
            >
              Distribute equally
            </button>
          )}
        </div>

        <div className={styles.memberList}>
          {expense_group.members.map((member) => {
            const edit = edits[member.user_id];
            const canEdit = isAdmin || member.user_id === current_user?.id;
            const canRemove = isAdmin && member.user_id !== current_user?.id;
            const memberCanEditRole = canEditRole(member);

            return (
              <div key={member.user_id} className={styles.memberRow}>
                <div className={styles.memberIdentity}>
                  <div className={styles.memberAvatar}>
                    {(member.user?.firstname ??
                      member.user?.username ??
                      "?")[0].toUpperCase()}
                  </div>
                  <div className={styles.memberInfo}>
                    <span className={styles.memberName}>
                      {member.user?.firstname || member.user?.lastname
                        ? `${member.user?.firstname ?? ""} ${member.user?.lastname ?? ""}`.trim()
                        : member.user?.username}
                      {member.user_id === current_user?.id ? " (you)" : ""}
                    </span>
                    <span className={styles.memberUsername}>
                      @{member.user?.username}
                    </span>
                  </div>
                </div>

                <div className={styles.memberControls}>
                  <Select
                    value={edit.role}
                    onChange={(v) => updateEdit(member.user_id, "role", v)}
                    options={[
                      { value: "member", label: "Member" },
                      { value: "admin", label: "Admin" },
                    ]}
                    wrapperClassName={styles.roleSelect}
                    disabled={!memberCanEditRole}
                  />

                  {canEdit ? (
                    <div className={styles.shareInputWrap}>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        className={styles.shareInput}
                        value={edit.default_split_ratio}
                        onChange={(e) =>
                          updateEdit(
                            member.user_id,
                            "default_split_ratio",
                            e.target.value,
                          )
                        }
                      />
                      <span className={styles.shareSuffix}>%</span>
                    </div>
                  ) : (
                    <span className={styles.ratioDisplay}>
                      {edit.default_split_ratio}%
                    </span>
                  )}

                  {canRemove ? (
                    <button
                      className={styles.removeBtn}
                      onClick={() => setConfirmRemove(member)}
                    >
                      <Icon icon="ph:x" width={14} height={14} />
                    </button>
                  ) : (
                    <div className={styles.removePlaceholder} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {error && (
          <div className={styles.errorBanner}>
            <Icon icon="ph:warning-circle" width={16} height={16} />
            {error}
          </div>
        )}

        {success && (
          <div className={styles.successBanner}>
            <Icon icon="ph:check-circle" width={16} height={16} />
            {success}
          </div>
        )}

        <div className={styles.formActions}>
          <button onClick={onClose} className={styles.cancelBtn}>
            Cancel
          </button>
          <button
            onClick={handleSave}
            className={styles.saveBtn}
            disabled={isUpdating || !ratioValid}
          >
            Save changes
          </button>
        </div>
      </div>

      {confirmRemove && (
        <ConfirmModal
          title="Remove member?"
          message={`@${confirmRemove.user?.username} will be removed from this group.`}
          confirmLabel="Remove"
          danger
          onConfirm={() => handleRemove(confirmRemove)}
          onCancel={() => setConfirmRemove(null)}
        />
      )}
    </div>
  );
};

export default ManageMembersModal;
