import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQueries } from "@tanstack/react-query";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useExpenses, useExpenseGroups, queryKeys } from "@/hooks/queries";
import { expenseGroupsApi } from "@/api";
import type { ExpenseGroup } from "@/types";
import { CategoryBreakdownCard } from "@/components/CategoryBreakdownCard";
import styles from "./DashboardPage.module.scss";

export const DashboardPage = () => {
  const user = useAuthStore((s) => s.user);
  const { data: expenses = [], isLoading: expensesLoading } = useExpenses();
  const { data: groups = [], isLoading: groupsLoading } = useExpenseGroups();

  const currentMonth = new Date().getMonth();
  const currentYear = new Date().getFullYear();

  const monthlyTotal = useMemo(() => {
    return expenses
      .filter((e) => {
        if (e.is_deleted) return false;
        const date = new Date(e.created_at);
        return (
          date.getMonth() === currentMonth && date.getFullYear() === currentYear
        );
      })
      .reduce((sum, e) => sum + e.value, 0);
  }, [expenses, currentMonth, currentYear]);

  const recentExpenses = useMemo(() => {
    return [...expenses]
      .filter((e) => !e.is_deleted && !e.expense_group_id)
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      .slice(0, 5);
  }, [expenses]);

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.greeting}>
            {greeting()}, {user?.firstname || user?.username}
          </h1>
          <p className={styles.subheading}>Here's your spending overview</p>
        </div>
        {/* <div className={styles.actions}>
          <Link to="/expenses" className={styles.actionBtn}>
            <Icon icon="ph:plus" width={16} height={16} />
            Add expense
          </Link>
          <Link to="/expense_groups" className={styles.actionBtnSecondary}>
            <Icon icon="ph:users-three" width={16} height={16} />
            New group
          </Link>
        </div> */}
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>
            <Icon icon="ph:calendar" width={16} height={16} />
            This month
          </div>
          <div className={styles.statValue}>€{monthlyTotal.toFixed(2)}</div>
          <p className={styles.statSub}>personal expenses</p>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statLabel}>
            <Icon icon="ph:users-three" width={16} height={16} />
            Groups
          </div>
          <div className={styles.statValue}>{groups.length}</div>
          <p className={styles.statSub}>active groups</p>
        </div>

        <BalanceSummary groups={groups} userId={user?.id ?? 0} />
      </div>

      <CategoryBreakdownCard />

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Recent personal expenses</h2>
          <Link to="/expenses" className={styles.seeAll}>
            See all <Icon icon="ph:arrow-right" width={14} height={14} />
          </Link>
        </div>

        {expensesLoading ? (
          <div className={styles.loading}>
            <Icon
              icon="ph:circle-notch"
              width={20}
              height={20}
              className={styles.spin}
            />
          </div>
        ) : recentExpenses.length === 0 ? (
          <div className={styles.empty}>
            <Icon icon="ph:receipt" width={32} height={32} />
            <p>No expenses yet</p>
            <Link to="/expenses" className={styles.emptyAction}>
              Add your first expense
            </Link>
          </div>
        ) : (
          <div className={styles.expenseList}>
            {recentExpenses.map((expense) => (
              <div key={expense.id} className={styles.expenseItem}>
                <div className={styles.expenseIcon}>
                  <Icon icon="ph:receipt" width={18} height={18} />
                </div>
                <div className={styles.expenseInfo}>
                  <span className={styles.expenseName}>{expense.name}</span>
                  <span className={styles.expenseDate}>
                    {expense.paid_at
                      ? new Date(expense.paid_at).toLocaleDateString("en-FI", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                          hour12: true,
                        })
                      : ""}
                  </span>
                </div>
                <span className={styles.expenseValue}>
                  €{expense.value.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Your groups</h2>
          <Link to="/expense_groups" className={styles.seeAll}>
            See all <Icon icon="ph:arrow-right" width={14} height={14} />
          </Link>
        </div>

        {groupsLoading ? (
          <div className={styles.loading}>
            <Icon
              icon="ph:circle-notch"
              width={20}
              height={20}
              className={styles.spin}
            />
          </div>
        ) : groups.length === 0 ? (
          <div className={styles.empty}>
            <Icon icon="ph:users-three" width={32} height={32} />
            <p>No groups yet</p>
            <Link to="/expense_groups" className={styles.emptyAction}>
              Create your first group
            </Link>
          </div>
        ) : (
          <div className={styles.groupGrid}>
            {groups.slice(0, 4).map((group) => (
              <Link
                key={group.id}
                to={`/expense_groups/${group.id}`}
                className={styles.groupCard}
              >
                <div className={styles.groupAvatar}>
                  {group.name[0].toUpperCase()}
                </div>
                <div className={styles.groupInfo}>
                  <span className={styles.groupName}>{group.name}</span>
                  <span className={styles.groupMembers}>
                    {group.members.length} member
                    {group.members.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <Icon
                  icon="ph:arrow-right"
                  width={16}
                  height={16}
                  className={styles.groupArrow}
                />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Balance summary card — fetches settlement per group and aggregates
const BalanceSummary = ({
  groups,
  userId,
}: {
  groups: ExpenseGroup[];
  userId: number;
}) => {
  const settlementQueries = useQueries({
    queries: groups.map((g) => ({
      queryKey: queryKeys.settlement(g.id),
      queryFn: () =>
        expenseGroupsApi.getSettlement(g.id).then((r) => r.data.data),
    })),
  });

  if (groups.length === 0) {
    return (
      <div className={styles.statCard}>
        <div className={styles.statLabel}>
          <Icon icon="ph:arrows-left-right" width={16} height={16} />
          Net balance
        </div>
        <div className={styles.statValue}>€0.00</div>
        <p className={styles.statSub}>across all groups</p>
      </div>
    );
  }

  const isLoading = settlementQueries.some((q) => q.isLoading);
  const balance = settlementQueries.reduce((sum, q) => {
    const member = q.data?.members.find((m) => m.user_id === userId);
    return sum + (member?.balance ?? 0);
  }, 0);

  const balanceLabel =
    balance > 0 ? "you'll get back" : balance < 0 ? "you owe" : "settled up";

  return (
    <div className={styles.statCard}>
      <div className={styles.statLabel}>
        <Icon icon="ph:arrows-left-right" width={16} height={16} />
        Net balance
      </div>
      {isLoading ? (
        <Icon
          icon="ph:circle-notch"
          width={22}
          height={22}
          className={styles.spin}
        />
      ) : (
        <div
          className={`${styles.statValue} ${
            balance > 0 ? styles.positive : balance < 0 ? styles.negative : ""
          }`}
        >
          €{Math.abs(balance).toFixed(2)}
        </div>
      )}
      <p className={styles.statSub}>{balanceLabel}</p>
    </div>
  );
};
