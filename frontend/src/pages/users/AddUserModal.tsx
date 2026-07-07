import { Icon } from "@iconify/react";
import styles from "./AddUserModal.module.scss";
import { useCreateUser } from "@/hooks/queries";
import { useState } from "react";
import { Select } from "@/components/ui/Select";

const newUserInitialState = {
  username: "",
  email: "",
  password: "",
  firstname: "",
  lastname: "",
  phone_number: "",
  role: "member" as "admin" | "member",
};

interface Props {
  onClose: () => void;
}

const AddUserModal = ({ onClose }: Props) => {
  const { mutate: createUser, isPending: isCreating } = useCreateUser();
  const [createForm, setCreateForm] = useState(newUserInitialState);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createUser(createForm, {
      onSuccess: () => onClose(),
    });
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.formHeader}>
          <h2 className={styles.formTitle}>New user</h2>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form
          id="add-user-form"
          onSubmit={handleCreate}
          className={styles.form}
        >
          <div className={styles.formRow}>
            <div className={styles.field}>
              <label className={styles.label}>First name*</label>
              <input
                className={styles.input}
                value={createForm.firstname}
                onChange={(e) =>
                  setCreateForm({ ...createForm, firstname: e.target.value })
                }
                required
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Last name*</label>
              <input
                className={styles.input}
                value={createForm.lastname}
                onChange={(e) =>
                  setCreateForm({ ...createForm, lastname: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.field}>
              <label className={styles.label}>Username*</label>
              <input
                className={styles.input}
                value={createForm.username}
                onChange={(e) =>
                  setCreateForm({ ...createForm, username: e.target.value })
                }
                required
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Email*</label>
              <input
                type="email"
                className={styles.input}
                value={createForm.email}
                onChange={(e) =>
                  setCreateForm({ ...createForm, email: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.field}>
              <label className={styles.label}>Password</label>
              <input
                type="password"
                className={styles.input}
                value={createForm.password}
                onChange={(e) =>
                  setCreateForm({ ...createForm, password: e.target.value })
                }
                placeholder="••••••••"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Phone number</label>
              <input
                type="text"
                className={styles.input}
                value={createForm.phone_number}
                onChange={(e) =>
                  setCreateForm({ ...createForm, phone_number: e.target.value })
                }
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Role</label>
            <Select
              triggerClassName={styles.dropdownTrigger}
              value={createForm.role}
              onChange={(v) =>
                setCreateForm({ ...createForm, role: v as "admin" | "member" })
              }
              options={[
                { value: "member", label: "Member" },
                { value: "admin", label: "Admin" },
              ]}
            />
          </div>
        </form>

        <div className={styles.formActions}>
          <button type="button" onClick={onClose} className={styles.cancelBtn}>
            Cancel
          </button>
          <button
            type="submit"
            form="add-user-form"
            className={styles.submitBtn}
            disabled={isCreating}
          >
            {isCreating && (
              <Icon
                icon="ph:circle-notch"
                width={16}
                height={16}
                className={styles.spin}
              />
            )}
            Create user
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddUserModal;
