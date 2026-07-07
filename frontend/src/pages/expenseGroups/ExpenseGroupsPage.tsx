import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "@iconify/react";
import {
  useExpenseGroups,
  useDeleteExpenseGroup,
  useLeaveExpenseGroup,
} from "@/hooks/queries";
import { useAuthStore } from "@/stores/authStore";
import type { ExpenseGroup } from "@/types";
import styles from "./ExpenseGroupsPage.module.scss";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import ExpenseGroupFormModal from "./common/ExpenseGroupFormModal";

export const ExpenseGroupsPage = () => {
  const user = useAuthStore((s) => s.user);
  const { data: expense_groups = [], isLoading } = useExpenseGroups();
  const [error, setError] = useState("");

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const { mutate: deleteGroup } = useDeleteExpenseGroup();
  const { mutate: leaveGroup } = useLeaveExpenseGroup();

  const [selectedExpenseGroupId, setSelectedExpenseGroupId] = useState<
    number | null
  >(null);
  const selectedExpenseGroup =
    expense_groups.find((g) => g.id === selectedExpenseGroupId) ?? null;

  const [showExpenseGroupFormModal, setShowExpenseGroupFormModal] =
    useState(false);
  const [
    showConfirmDeleteExpenseGroupModal,
    setShowConfirmDeleteExpenseGroupModal,
  ] = useState(false);
  const [
    showConfirmLeaveExpenseGroupModal,
    setShowConfirmLeaveExpenseGroupModal,
  ] = useState(false);

  const toggleExpenseGroupFormModal = (
    open: boolean,
    expenseGroup?: ExpenseGroup,
  ) => {
    setSelectedExpenseGroupId(expenseGroup ? expenseGroup.id : null);
    setShowExpenseGroupFormModal(open);
  };

  const toggleConfirmDeleteExpenseGroup = (
    open: boolean,
    expenseGroup?: ExpenseGroup,
  ) => {
    setSelectedExpenseGroupId(expenseGroup ? expenseGroup.id : null);
    setShowConfirmDeleteExpenseGroupModal(open);
  };

  const handleConfirmDelete = () => {
    if (selectedExpenseGroupId) {
      setError("");
      toggleConfirmDeleteExpenseGroup(false);
      deleteGroup(selectedExpenseGroupId, {
        onError: () => {
          setError("Failed to delete expense group. Please try again.");
        },
      });
    }
  };

  const toggleConfirmLeaveExpenseGroup = (
    open: boolean,
    expenseGroup?: ExpenseGroup,
  ) => {
    setSelectedExpenseGroupId(expenseGroup ? expenseGroup.id : null);
    setShowConfirmLeaveExpenseGroupModal(open);
  };

  const handleConfirmLeave = () => {
    if (selectedExpenseGroupId) {
      setError("");
      toggleConfirmDeleteExpenseGroup(false);
      leaveGroup(selectedExpenseGroupId, {
        onError: () => {
          setError("Failed to leave expense group. Please try again.");
        },
      });
    }
  };

  const isAdmin = (expense_group: (typeof expense_groups)[0]) =>
    expense_group.members.some(
      (m) => m.user_id === user?.id && m.role === "admin",
    );

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Groups</h1>
          <p className={styles.subtitle}>Shared expenses with others</p>
        </div>
        <button
          className={styles.addBtn}
          onClick={() => toggleExpenseGroupFormModal(true)}
        >
          <Icon icon="ph:plus" width={16} height={16} />
          Add group
        </button>
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
      ) : expense_groups.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:users-three" width={40} height={40} />
          <p>No expense groups yet</p>
          <button
            className={styles.emptyAction}
            onClick={() => toggleExpenseGroupFormModal(true)}
          >
            Create your first expense group
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {expense_groups.map((expense_group) => (
            <div key={expense_group.id} className={styles.card}>
              <Link
                to={`/expense_groups/${expense_group.id}`}
                className={styles.cardMain}
              >
                <div className={styles.cardAvatar}>
                  {expense_group.name[0].toUpperCase()}
                </div>
                <div className={styles.cardInfo}>
                  <div className={styles.cardNameRow}>
                    <span className={styles.cardName}>
                      {expense_group.name}
                    </span>
                    {isAdmin(expense_group) && (
                      <span className={styles.adminBadge}>admin</span>
                    )}
                  </div>
                  {expense_group.description && (
                    <span className={styles.cardDesc}>
                      {expense_group.description}
                    </span>
                  )}
                  <div className={styles.cardMeta}>
                    <Icon icon="ph:users" width={13} height={13} />
                    {expense_group.members.length} member
                    {expense_group.members.length !== 1 ? "s" : ""}
                  </div>
                </div>
              </Link>

              <div className={styles.cardFooter}>
                <div className={styles.memberAvatars}>
                  {expense_group.members.slice(0, 4).map((m) => (
                    <div
                      key={m.user_id}
                      className={styles.memberAvatar}
                      title={m.user?.username}
                    >
                      {m.user?.username?.[0]?.toUpperCase() ?? "?"}
                    </div>
                  ))}
                  {expense_group.members.length > 4 && (
                    <div className={styles.memberAvatarMore}>
                      +{expense_group.members.length - 4}
                    </div>
                  )}
                </div>

                <div className={styles.cardActions}>
                  {isAdmin(expense_group) ? (
                    <button
                      className={styles.dangerBtn}
                      onClick={() =>
                        toggleConfirmDeleteExpenseGroup(true, expense_group)
                      }
                    >
                      <Icon icon="ph:trash" width={15} height={15} />
                      Delete
                    </button>
                  ) : (
                    <button
                      className={styles.dangerBtn}
                      onClick={() =>
                        toggleConfirmLeaveExpenseGroup(true, expense_group)
                      }
                    >
                      <Icon icon="ph:sign-out" width={15} height={15} />
                      Leave
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showExpenseGroupFormModal && (
        <ExpenseGroupFormModal
          expenseGroup={selectedExpenseGroup}
          isEditing={!!selectedExpenseGroup}
          onClose={() => toggleExpenseGroupFormModal(false)}
        />
      )}

      {showConfirmDeleteExpenseGroupModal && selectedExpenseGroup && (
        <ConfirmModal
          title="Delete group?"
          message={`"${selectedExpenseGroup.name}" and all its expenses will be permanently deleted.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleConfirmDelete}
          onCancel={() => toggleConfirmDeleteExpenseGroup(false)}
        />
      )}

      {showConfirmLeaveExpenseGroupModal && selectedExpenseGroup && (
        <ConfirmModal
          title="Leave group?"
          message={`You will lose access to "${selectedExpenseGroup.name}".`}
          confirmLabel="Leave"
          danger
          onConfirm={handleConfirmLeave}
          onCancel={() => toggleConfirmLeaveExpenseGroup(false)}
        />
      )}
    </div>
  );
};
