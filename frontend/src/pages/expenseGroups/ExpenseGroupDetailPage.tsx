import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Icon } from "@iconify/react";
import {
  useExpenseGroup,
  useSettlement,
  useExpenses,
  useLeaveExpenseGroup,
  useDeleteExpenseGroup,
} from "@/hooks/queries";
import { useAuthStore } from "@/stores/authStore";
import styles from "./ExpenseGroupDetailPage.module.scss";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import ExpensesTab from "./tabs/ExpensesTab";
import MembersTab from "./tabs/MembersTab";
import SettlementTab from "./tabs/SettlementTab";

type Tab = "expenses" | "members" | "settlement";

export const ExpenseGroupDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const groupId = Number(id);
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const { data: expense_group, isLoading: groupLoading } =
    useExpenseGroup(groupId);
  const { data: expenses = [] } = useExpenses({ expense_group_id: groupId });
  const { data: settlement } = useSettlement(groupId);

  const { mutate: leaveGroup } = useLeaveExpenseGroup();
  const { mutate: deleteGroup } = useDeleteExpenseGroup();

  const [tab, setTab] = useState<Tab>("expenses");

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);

  const currentSettlement = settlement?.members.find(
    (m) => m.user_id === user?.id,
  );

  const balance = currentSettlement?.balance ?? 0;
  const balanceLabel =
    balance > 0 ? "You'll get back" : balance < 0 ? "You owe" : "Settled up";

  if (groupLoading) {
    return (
      <div className={styles.loading}>
        <Icon
          icon="ph:circle-notch"
          width={24}
          height={24}
          className={styles.spin}
        />
      </div>
    );
  }

  if (!expense_group) {
    return (
      <div className={styles.notFound}>
        <Icon icon="ph:warning" width={40} height={40} />
        <p>Group not found</p>
      </div>
    );
  }

  const isAdmin = expense_group.members.some(
    (m) => m.user_id === user?.id && m.role === "admin",
  );

  const handleLeave = () => {
    setConfirmLeave(false);
    leaveGroup(groupId, { onSuccess: () => navigate("/expense_groups") });
  };

  const handleDelete = () => {
    setConfirmDelete(false);
    deleteGroup(groupId, { onSuccess: () => navigate("/expense_groups") });
  };

  const activeExpenses = expenses.filter((e) => !e.is_deleted);
  const totalSpent = activeExpenses.reduce((sum, e) => sum + e.value, 0);

  return (
    <div className={styles.page}>
      <div className={styles.topBar}>
        <button
          onClick={() => navigate("/expense_groups")}
          className={styles.backBtn}
        >
          <Icon icon="ph:arrow-left" width={18} height={18} />
          <span>Groups</span>
        </button>
      </div>

      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <div className={styles.groupAvatar}>
            {expense_group.name[0].toUpperCase()}
          </div>
          <div>
            <h1 className={styles.title}>{expense_group.name}</h1>
            {expense_group.description && (
              <p className={styles.subtitle}>{expense_group.description}</p>
            )}
          </div>
        </div>
        <div className={styles.headerActions}>
          {isAdmin ? (
            <button
              className={styles.dangerBtn}
              onClick={() => setConfirmDelete(true)}
            >
              <Icon icon="ph:trash" width={16} height={16} />
              Delete
            </button>
          ) : (
            <button
              className={styles.dangerBtn}
              onClick={() => setConfirmLeave(true)}
            >
              <Icon icon="ph:sign-out" width={16} height={16} />
              Leave
            </button>
          )}
        </div>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total group spent</span>
          <span className={styles.statValue}>€{totalSpent.toFixed(2)}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Members</span>
          <span className={styles.statValue}>
            {expense_group.members.length}
          </span>
        </div>

        {currentSettlement && (
          <>
            <div className={styles.stat}>
              <span className={styles.statLabel}>You paid</span>
              <span className={styles.statValue}>
                €{currentSettlement.paid.toFixed(2)}
              </span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statLabel}>Your share</span>
              <span className={styles.statValue}>
                €{currentSettlement.should_pay.toFixed(2)}
              </span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statLabel}>{balanceLabel}</span>
              <span
                className={`${styles.statValue} ${
                  balance > 0
                    ? styles.positive
                    : balance < 0
                      ? styles.negative
                      : ""
                }`}
              >
                €{Math.abs(balance).toFixed(2)}
              </span>
            </div>
          </>
        )}
      </div>

      <div className={styles.tabs}>
        {(["expenses", "members", "settlement"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`${styles.tab} ${tab === t ? styles.tabActive : ""}`}
            onClick={() => setTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === "expenses" && <ExpensesTab expense_group={expense_group} />}

      {tab === "members" && <MembersTab expense_group={expense_group} />}

      {tab === "settlement" && (
        <SettlementTab
          settlement={settlement}
          expense_group={expense_group}
          expenses={expenses}
        />
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete group?"
          message={`"${expense_group.name}" and all its expenses will be permanently deleted.`}
          confirmLabel="Delete"
          danger
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}

      {confirmLeave && (
        <ConfirmModal
          title="Leave group?"
          message={`You will lose access to "${expense_group.name}".`}
          confirmLabel="Leave"
          danger
          onConfirm={handleLeave}
          onCancel={() => setConfirmLeave(false)}
        />
      )}
    </div>
  );
};
