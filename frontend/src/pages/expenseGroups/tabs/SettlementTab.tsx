import {
  Expense,
  ExpenseGroup,
  Settlement,
  TransactionWithUserInfo,
} from "@/types";
import styles from "./SettlementTab.module.scss";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useState } from "react";
import { ExpenseDetailsModal } from "@/pages/expenses/ExpenseDetailsModal";
import { useCategories } from "@/hooks/queries";
import { RepaymentModal } from "../common/RepaymentModal";
import { displayName } from "@/utils/user";
import RepaymentHistory from "../common/RepaymentHistory";

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
  const [showConfirmResolveModal, setShowConfirmResolveModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<TransactionWithUserInfo | null>(null);

  const selectedExpense =
    expenses.find((e) => e.id === selectedExpenseId) ?? null;

  const isGroupAdmin = expense_group.members.some(
    (m) => m.user_id === current_user?.id && m.role === "admin",
  );

  const showResolveBtn = (allowed_ids: number[]) => {
    if (!current_user) return false;
    if (current_user.role === "admin" || isGroupAdmin) {
      return true;
    }
    return allowed_ids.some((id) => id === current_user.id);
  };

  const toggleExpenseDetailsModal = (open: boolean, expense_id?: number) => {
    setSelectedExpenseId(expense_id ? expense_id : null);
    setShowExpenseDetailsModal(open);
  };

  const toggleConfirmResolve = (
    open: boolean,
    transaction: TransactionWithUserInfo | null,
  ) => {
    setSelectedTransaction(transaction ?? null);
    setShowConfirmResolveModal(open);
  };

  return (
    <div className={styles.section}>
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
          <div className={styles.block}>
            <p className={styles.summary}>
              <strong>€{settlement.total.toFixed(2)}</strong> total
              {settlement.pending_total > 0 && (
                <>
                  {" · "}
                  <span className={styles.summaryPending}>
                    <strong>€{settlement.pending_total.toFixed(2)}</strong>{" "}
                    awaiting split
                  </span>
                </>
              )}
            </p>

            <div className={styles.settlementGrid}>
              {settlement.members.map((member) => {
                const isZero = Math.abs(member.balance) < 0.005;
                const sign = isZero ? "" : member.balance > 0 ? "+" : "-";
                return (
                  <div key={member.user_id} className={styles.settlementCard}>
                    <div className={styles.settlementAvatar}>
                      {displayName(member)[0]?.toUpperCase() ?? "?"}
                    </div>
                    <div className={styles.settlementInfo}>
                      <div className={styles.settlementNameContainer}>
                        <div className={styles.settlementName}>
                          {displayName(member)}
                          {member.user_id === current_user?.id ? " (you)" : ""}
                        </div>
                        <div className={styles.settlementUsername}>
                          {member?.username ? "@" + member.username : ""}
                        </div>
                      </div>
                      <div className={styles.settlementRow}>
                        <span className={styles.settlementLabel}>Paid</span>
                        <span>€{member.paid.toFixed(2)}</span>
                      </div>
                      <div className={styles.settlementRow}>
                        <span className={styles.settlementLabel}>
                          Should pay
                        </span>
                        <span>€{member.should_pay.toFixed(2)}</span>
                      </div>
                    </div>
                    <span
                      className={`${styles.balance} ${
                        isZero
                          ? styles.neutral
                          : member.balance > 0
                            ? styles.positive
                            : styles.negative
                      }`}
                    >
                      {sign}€{Math.abs(member.balance).toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {settlement.transactions.length === 0 &&
            settlement.pending_expenses.length === 0 &&
            settlement.total > 0 && (
              <div className={styles.allSettled}>
                <Icon icon="ph:check-circle" width={18} height={18} />
                <span>All settled up</span>
              </div>
            )}

          {settlement.transactions.length > 0 && (
            <div className={styles.block}>
              <h3 className={styles.transactionTitle}>Who pays who</h3>
              <div className={styles.transactions}>
                {settlement.transactions.map((t) => {
                  const from = settlement.members.find(
                    (m) => m.user_id === t.from_user_id,
                  );
                  const to = settlement.members.find(
                    (m) => m.user_id === t.to_user_id,
                  );
                  return (
                    <div
                      key={`${t.from_user_id}-${t.to_user_id}`}
                      className={styles.transaction}
                    >
                      <div className={styles.txInfo}>
                        <div className={styles.txPeople}>
                          <span className={styles.txName}>
                            {displayName(from)}
                            {t.from_user_id === current_user?.id
                              ? " (you)"
                              : ""}
                          </span>{" "}
                          →{" "}
                          <span className={styles.txName}>
                            {displayName(to)}
                            {t.to_user_id === current_user?.id ? " (you)" : ""}
                          </span>
                        </div>
                      </div>
                      <div className={styles.txRight}>
                        <div className={styles.txActions}>
                          {showResolveBtn([t.from_user_id, t.to_user_id]) && (
                            <button
                              title="Mark as paid"
                              className={styles.resolveBtn}
                              onClick={() =>
                                toggleConfirmResolve(true, {
                                  ...t,
                                  from_user: from,
                                  to_user: to,
                                })
                              }
                            >
                              Resolve
                            </button>
                          )}
                        </div>
                        <span className={styles.txAmount}>
                          €{t.amount.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {settlement.pending_expenses.length > 0 && (
            <div className={styles.block}>
              <div className={styles.pendingBanner}>
                <Icon icon="ph:warning-circle" width={18} height={18} />
                <span>
                  {settlement.pending_expenses.length} expense
                  {settlement.pending_expenses.length > 1 ? "s" : ""} need
                  {settlement.pending_expenses.length > 1 ? "" : "s"} a split
                  ratio before they count in balances.
                </span>
              </div>
              <div className={styles.pendingList}>
                {settlement.pending_expenses.map((pe) => {
                  const payee = settlement.members.find(
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
                          Paid by {payee?.username ?? pe.payee_id}
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
            </div>
          )}
          <RepaymentHistory expense_group={expense_group} />
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

      {showConfirmResolveModal && selectedTransaction && (
        <RepaymentModal
          expense_group_id={expense_group.id}
          transaction={selectedTransaction}
          onClose={() => toggleConfirmResolve(false, null)}
        />
      )}
    </div>
  );
};

export default SettlementTab;
