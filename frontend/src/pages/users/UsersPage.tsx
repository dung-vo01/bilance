import { useMemo, useState } from "react";
import { Icon } from "@iconify/react";
import { useUsers, useDeleteUser } from "@/hooks/queries";
import { UserDetailModal } from "./UserDetailModal";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import type { User } from "@/types";
import styles from "./UsersPage.module.scss";
import AddUserModal from "./AddUserModal";
import { Select } from "@/components/ui/Select";

type SortBy = "name" | "created";
type RoleFilter = "all" | "admin" | "member";

export const UsersPage = () => {
  const [searchKw, setSearchKw] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("name");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<User | null>(null);
  const { data: users = [], isLoading } = useUsers({ search_kw: searchKw });
  const { mutate: deleteUser } = useDeleteUser();

  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const selectedUser = users.find((u) => u.id === selectedUserId) ?? null;

  const filteredUsers = useMemo(() => {
    let result = [...(users ?? [])];

    if (roleFilter !== "all") {
      result = result.filter((u) => u.role === roleFilter);
    }

    result.sort((a, b) => {
      if (sortBy === "name") {
        const nameA =
          `${a.firstname ?? ""} ${a.lastname ?? ""}`.trim() || a.username;
        const nameB =
          `${b.firstname ?? ""} ${b.lastname ?? ""}`.trim() || b.username;
        return nameA.localeCompare(nameB);
      }
      if (sortBy === "created") {
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }
      return 0;
    });

    return result;
  }, [users, roleFilter, sortBy]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Users</h1>
          <p className={styles.subtitle}>Manage all registered users</p>
        </div>
        <button
          className={styles.addBtn}
          onClick={() => setShowCreateForm(true)}
        >
          <Icon icon="ph:plus" width={16} height={16} />
          Add user
        </button>
      </div>

      <div className={styles.searchBar}>
        <Icon
          icon="ph:magnifying-glass"
          width={18}
          height={18}
          className={styles.searchIcon}
        />
        <input
          className={styles.searchInput}
          value={searchKw}
          onChange={(e) => setSearchKw(e.target.value)}
          placeholder="Search by name, username or email..."
        />
      </div>

      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {(["all", "admin", "member"] as RoleFilter[]).map((r) => (
            <button
              key={r}
              className={`${styles.filterBtn} ${roleFilter === r ? styles.filterActive : ""}`}
              onClick={() => setRoleFilter(r)}
            >
              {r.charAt(0).toUpperCase() + r.slice(1)}
            </button>
          ))}
        </div>

        <div className={styles.sortRow}>
          <span className={styles.sortLabel}>Sort by</span>
          <Select
            value={sortBy}
            onChange={(v) => setSortBy(v as SortBy)}
            options={[
              { value: "name", label: "Name" },
              { value: "created", label: "Date created" },
            ]}
          />
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>
          <Icon
            icon="ph:circle-notch"
            width={24}
            height={24}
            className={styles.spin}
          />
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:users" width={40} height={40} />
          <p>No users found</p>
        </div>
      ) : (
        <div className={styles.list}>
          {filteredUsers.map((user) => (
            <div
              key={user.id}
              className={`${styles.item} ${!user.is_active ? styles.itemInactive : ""}`}
              onClick={() => setSelectedUserId(user.id)}
            >
              <div className={styles.avatar}>
                {user.username[0].toUpperCase()}
              </div>
              <div className={styles.info}>
                <div className={styles.nameRow}>
                  <span className={styles.name}>
                    {user.firstname || user.lastname
                      ? `${user.firstname ?? ""} ${user.lastname ?? ""}`.trim()
                      : user.username}
                  </span>
                  <span
                    className={`${styles.roleBadge} ${user.role === "admin" ? styles.roleAdmin : styles.roleMember}`}
                  >
                    {user.role}
                  </span>
                  {!user.is_active && (
                    <span className={styles.inactiveBadge}>inactive</span>
                  )}
                </div>
                <span className={styles.username}>@{user.username}</span>
                <span className={styles.email}>{user.email}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedUser && (
        <UserDetailModal
          user={selectedUser}
          onClose={() => setSelectedUserId(null)}
          onDelete={(user) => {
            setConfirmDelete(user);
          }}
        />
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete user?"
          message={`@${confirmDelete.username} will be permanently deleted.`}
          confirmLabel="Delete"
          danger
          onConfirm={() => {
            deleteUser(confirmDelete.id);
            setConfirmDelete(null);
            setSelectedUserId(null);
          }}
          onCancel={() => setConfirmDelete(null)}
        />
      )}

      {showCreateForm && (
        <AddUserModal onClose={() => setShowCreateForm(false)} />
      )}
    </div>
  );
};
