import { useState } from "react";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useUpdateUser } from "@/hooks/queries";
import type { UpdateUserPayload } from "@/types";
import styles from "./ProfilePage.module.scss";

export const ProfilePage = () => {
  const { user, logout } = useAuthStore();
  const { mutate: updateUser, isPending } = useUpdateUser();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<UpdateUserPayload>({
    firstname: user?.firstname ?? "",
    lastname: user?.lastname ?? "",
    phone_number: user?.phone_number ?? "",
  });
  const [saved, setSaved] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    updateUser(
      { id: user.id, data: form },
      {
        onSuccess: () => {
          setEditing(false);
          setSaved(true);
          setTimeout(() => setSaved(false), 2500);
        },
      },
    );
  };

  const handleCancel = () => {
    setForm({
      firstname: user?.firstname ?? "",
      lastname: user?.lastname ?? "",
      phone_number: user?.phone_number ?? "",
    });
    setEditing(false);
  };

  if (!user) return null;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Profile</h1>
        <p className={styles.subtitle}>Manage your account</p>
      </div>

      <div className={styles.card}>
        <div className={styles.avatarRow}>
          <div className={styles.avatar}>{user.username[0].toUpperCase()}</div>
          <div className={styles.avatarInfo}>
            <span className={styles.username}>@{user.username}</span>
            <span className={styles.email}>{user.email}</span>
            <span className={styles.roleBadge}>{user.role}</span>
          </div>
        </div>

        <div className={styles.divider} />

        {saved && (
          <div className={styles.successBanner}>
            <Icon icon="ph:check-circle" width={16} height={16} />
            Profile updated successfully
          </div>
        )}

        {editing ? (
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>First name</label>
                <input
                  className={styles.input}
                  value={form.firstname ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, firstname: e.target.value })
                  }
                  placeholder="Dung"
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
                  placeholder="Vu"
                />
              </div>
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Phone number</label>
              <div className={styles.inputWrap}>
                <Icon
                  icon="ph:phone"
                  className={styles.inputIcon}
                  width={16}
                  height={16}
                />
                <input
                  className={styles.input}
                  value={form.phone_number ?? ""}
                  onChange={(e) =>
                    setForm({ ...form, phone_number: e.target.value || null })
                  }
                  placeholder="+358 40 123 4567"
                />
              </div>
            </div>

            <div className={styles.formActions}>
              {isPending && (
                <Icon
                  icon="ph:circle-notch"
                  width={16}
                  height={16}
                  className={styles.spin}
                />
              )}
              <button
                type="button"
                onClick={handleCancel}
                className={styles.cancelBtn}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={styles.submitBtn}
                disabled={isPending}
              >
                Save changes
              </button>
            </div>
          </form>
        ) : (
          <div className={styles.infoGrid}>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>First name</span>
              <span className={styles.infoValue}>{user.firstname || "—"}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Last name</span>
              <span className={styles.infoValue}>{user.lastname || "—"}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Phone</span>
              <span className={styles.infoValue}>
                {user.phone_number || "—"}
              </span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Username</span>
              <span className={styles.infoValue}>@{user.username}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>Email</span>
              <span className={styles.infoValue}>{user.email}</span>
            </div>

            <div className={styles.editRow}>
              <button
                className={styles.editBtn}
                onClick={() => setEditing(true)}
              >
                <Icon icon="ph:pencil-simple" width={16} height={16} />
                Edit profile
              </button>
            </div>
          </div>
        )}
      </div>

      <div className={styles.dangerZone}>
        <h2 className={styles.dangerTitle}>Account</h2>
        <button
          className={styles.signOutBtn}
          onClick={() => {
            logout();
            window.location.href = "/login";
          }}
        >
          <Icon icon="ph:sign-out" width={16} height={16} />
          Sign out
        </button>
      </div>
    </div>
  );
};
