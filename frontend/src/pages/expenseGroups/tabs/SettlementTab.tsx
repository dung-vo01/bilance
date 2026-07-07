import { Expense, ExpenseGroup, Settlement } from "@/types";
import styles from "./SettlementTab.module.scss";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useState } from "react";
import { ExpenseDetailsModal } from "@/pages/expenses/ExpenseDetailsModal";
import { useCategories } from "@/hooks/queries";

type Props = {
  settlement: Settlement | undefined;
  expense_group: ExpenseGroup;
  expenses: Expense[];
};

const SettlementTab = ({ settlement, expense_group, expenses }: Props) => {
  const current_user = useAuthStore((s) => s.user);
  const { data: categories = [] } = useCategories({
    expense_group_id: expense_group.id,
  });

  const [selectedExpenseId, setSelectedExpenseId] = useState<number | null>(
    null,
  );
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

  const toggleExpenseDetailsModal = (open: boolean, expense_id?: number) => {
    setSelectedExpenseId(expense_id ? expense_id : null);
    setShowExpenseDetailsModal(open);
  };

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Settlement</h2>

      {!settlement ? (
        <div className={styles.empty}>
          <Icon
            icon="ph:circle-notch"
            width={24}
            height={24}
            className={styles.spin}
          />
        </div>
      ) : (
        <>
          <div className={styles.settlementStats}>
            <div className={styles.settlementStat}>
              <span className={styles.statLabel}>Total spent</span>
              <span className={styles.statValue}>
                €{settlement.total.toFixed(2)}
              </span>
            </div>
            <div className={styles.settlementStat}>
              <span className={styles.statLabel}>Settled</span>
              <span className={styles.statValue}>
                €{settlement.settled_total.toFixed(2)}
              </span>
            </div>
            {settlement.pending_total > 0 && (
              <div className={`${styles.settlementStat} ${styles.pendingStat}`}>
                <span className={styles.statLabel}>Pending split</span>
                <span className={styles.statValue}>
                  €{settlement.pending_total.toFixed(2)}
                </span>
              </div>
            )}
          </div>

          {settlement.pending_expenses.length > 0 && (
            <div className={styles.pendingBanner}>
              <Icon icon="ph:warning-circle" width={18} height={18} />
              <span>
                {settlement.pending_expenses.length} expense
                {settlement.pending_expenses.length > 1 ? "s" : ""} need
                {settlement.pending_expenses.length > 1 ? "" : "s"} a split
                ratio before they're included in balances.
              </span>
            </div>
          )}

          <div className={styles.settlementGrid}>
            {settlement.members.map((m) => {
              const member = expense_group.members.find(
                (gm) => gm.user_id === m.user_id,
              );
              return (
                <div key={m.user_id} className={styles.settlementCard}>
                  <div className={styles.settlementAvatar}>
                    {member?.user?.username?.[0]?.toUpperCase() ?? "?"}
                  </div>
                  <div className={styles.settlementInfo}>
                    <span className={styles.settlementName}>
                      {member?.user?.username ?? m.user_id}
                      {m.user_id === current_user?.id ? " (you)" : ""}
                    </span>
                    <div className={styles.settlementRow}>
                      <span className={styles.settlementLabel}>Paid</span>
                      <span>€{m.paid.toFixed(2)}</span>
                    </div>
                    <div className={styles.settlementRow}>
                      <span className={styles.settlementLabel}>Should pay</span>
                      <span>€{m.should_pay.toFixed(2)}</span>
                    </div>
                  </div>
                  <span
                    className={`${styles.balance} ${
                      m.balance >= 0 ? styles.positive : styles.negative
                    }`}
                  >
                    {m.balance >= 0 ? "+" : ""}€{m.balance.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>

          {settlement.transactions.length > 0 && (
            <>
              <h3 className={styles.transactionTitle}>Who pays who</h3>
              <div className={styles.transactions}>
                {settlement.transactions.map((t, i) => {
                  const from = expense_group.members.find(
                    (m) => m.user_id === t.from_user_id,
                  );
                  const to = expense_group.members.find(
                    (m) => m.user_id === t.to_user_id,
                  );
                  return (
                    <div key={i} className={styles.transaction}>
                      <span className={styles.txName}>
                        {from?.user?.username ?? t.from_user_id}
                        {t.from_user_id === current_user?.id ? " (you)" : ""}
                      </span>
                      <div className={styles.txArrow}>
                        <Icon icon="ph:arrow-right" width={16} height={16} />
                        <span className={styles.txAmount}>
                          €{t.amount.toFixed(2)}
                        </span>
                      </div>
                      <span className={styles.txName}>
                        {to?.user?.username ?? t.to_user_id}
                        {t.to_user_id === current_user?.id ? " (you)" : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {settlement.pending_expenses.length > 0 && (
            <>
              <h3 className={styles.transactionTitle}>Awaiting split</h3>
              <div className={styles.pendingList}>
                {settlement.pending_expenses.map((pe) => {
                  const payee = expense_group.members.find(
                    (m) => m.user_id === pe.payee_id,
                  );
                  return (
                    <div
                      key={pe.id}
                      className={styles.pendingItem}
                      onClick={() => toggleExpenseDetailsModal(true, pe.id)}
                    >
                      <div className={styles.pendingInfo}>
                        <span className={styles.pendingName}>
                          {pe.name || "Untitled expense"}
                        </span>
                        <span className={styles.pendingLabel}>
                          Paid by {payee?.user?.username ?? pe.payee_id}
                          {pe.payee_id === current_user?.id ? " (you)" : ""}
                        </span>
                      </div>
                      <span className={styles.pendingAmount}>
                        €{pe.value.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </>
      )}

      {showExpenseDetailsModal && selectedExpense && (
        <ExpenseDetailsModal
          expense={selectedExpense}
          categories={categories}
          expense_group={expense_group}
          onClose={() => toggleExpenseDetailsModal(false)}
        />
      )}
    </div>
  );
};

export default SettlementTab;
