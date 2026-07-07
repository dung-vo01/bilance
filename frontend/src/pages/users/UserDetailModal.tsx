import { useState } from "react";
import { Icon } from "@iconify/react";
import { useUpdateUser } from "@/hooks/queries";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import type { User, UpdateUserPayload } from "@/types";
import styles from "./UserDetailModal.module.scss";
import { Select } from "@/components/ui/Select";

interface Props {
  user: User;
  onClose: () => void;
  onDelete: (user: User) => void;
}

export const UserDetailModal = ({ user, onClose, onDelete }: Props) => {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<UpdateUserPayload>({
    firstname: user.firstname ?? "",
    lastname: user.lastname ?? "",
    phone_number: user.phone_number ?? "",
    role: user.role ?? "member",
  });
  const [confirmDeactivate, setConfirmDeactivate] = useState(false);

  const { mutate: updateUser } = useUpdateUser();

  const handleCancel = () => {
    setForm({
      firstname: user.firstname ?? "",
      lastname: user.lastname ?? "",
      phone_number: user.phone_number ?? "",
      role: user.role ?? "member",
    });
    setEditing(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateUser(
      { id: user.id, data: form },
      { onSuccess: () => setEditing(false) },
    );
  };

  const handleDeactivate = () => {
    updateUser(
      { id: user.id, data: { is_active: !user.is_active } },
      { onSuccess: () => setConfirmDeactivate(false) },
    );
  };

  const handleRoleChange = (role: "admin" | "member") => {
    updateUser({ id: user.id, data: { role } });
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>
            {editing ? "Edit user" : "User details"}
          </h2>
          <div className={styles.headerActions}>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className={styles.editBtn}
              >
                <Icon icon="ph:pencil-simple" width={16} height={16} />
              </button>
            )}
            <button onClick={onClose} className={styles.closeBtn}>
              <Icon icon="ph:x" width={18} height={18} />
            </button>
          </div>
        </div>

        <div className={styles.avatarSection}>
          <div
            className={`${styles.avatar} ${!user.is_active ? styles.avatarInactive : ""}`}
          >
            {user.username[0].toUpperCase()}
          </div>
          {!user.is_active && (
            <span className={styles.inactiveBadge}>Inactive</span>
          )}
        </div>

        {editing ? (
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.fields}>
              <div className={styles.field}>
                <label className={styles.label}>First name</label>
                <input
                  className={styles.input}
                  value={form.firstname ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, firstname: e.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Last name</label>
                <input
                  className={styles.input}
                  value={form.lastname ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, lastname: e.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Phone number</label>
                <input
                  className={styles.input}
                  value={form.phone_number ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, phone_number: e.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Role</label>
                <Select
                  triggerClassName={styles.dropdownTrigger}
                  value={form.role ?? ""}
                  onChange={(v) =>
                    setForm({
                      ...form,
                      role: v as "admin" | "member",
                    })
                  }
                  options={[
                    { value: "member", label: "Member" },
                    { value: "admin", label: "Admin" },
                  ]}
                />
              </div>
            </div>
            <div className={styles.formActions}>
              <button
                type="button"
                onClick={handleCancel}
                className={styles.cancelBtn}
              >
                Cancel
              </button>
              <button type="submit" className={styles.submitBtn}>
                Save changes
              </button>
            </div>
          </form>
        ) : (
          <div className={styles.detailGrid}>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Username</span>
              <span className={styles.detailValue}>@{user.username}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Name</span>
              <span className={styles.detailValue}>
                {user.firstname || user.lastname
                  ? `${user.firstname ?? ""} ${user.lastname ?? ""}`.trim()
                  : "—"}
              </span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Email</span>
              <span className={styles.detailValue}>{user.email ?? "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Phone</span>
              <span className={styles.detailValue}>
                {user.phone_number ?? "—"}
              </span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Role</span>
              <div className={styles.roleRow}>
                <span
                  className={`${styles.roleBadge} ${user.role === "admin" ? styles.roleAdmin : styles.roleMember}`}
                >
                  {user.role}
                </span>
                <button
                  className={styles.changeRoleBtn}
                  onClick={() =>
                    handleRoleChange(user.role === "admin" ? "member" : "admin")
                  }
                >
                  Make {user.role === "admin" ? "member" : "admin"}
                </button>
              </div>
            </div>
          </div>
        )}

        {!editing && (
          <div className={styles.modalFooter}>
            <button
              className={`${styles.footerBtn} ${user.is_active ? styles.deactivateBtn : styles.activateBtn}`}
              onClick={() => setConfirmDeactivate(true)}
            >
              <Icon
                icon={user.is_active ? "ph:pause" : "ph:play"}
                width={16}
                height={16}
              />
              {user.is_active ? "Deactivate" : "Reactivate"}
            </button>

            {!user.is_active && (
              <button
                className={styles.deleteBtn}
                onClick={() => onDelete(user)}
              >
                <Icon icon="ph:trash" width={16} height={16} />
                Delete
              </button>
            )}
          </div>
        )}
      </div>

      {confirmDeactivate && (
        <ConfirmModal
          title={user.is_active ? "Deactivate user?" : "Reactivate user?"}
          message={`@${user.username} will ${user.is_active ? "no longer be able to log in" : "be able to log in again"}.`}
          confirmLabel={user.is_active ? "Deactivate" : "Reactivate"}
          danger={user.is_active}
          onConfirm={handleDeactivate}
          onCancel={() => setConfirmDeactivate(false)}
        />
      )}
    </div>
  );
};
