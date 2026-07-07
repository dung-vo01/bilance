import { ExpenseGroup, User } from "@/types";
import styles from "./MembersTab.module.scss";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { Icon } from "@iconify/react";
import { useRemoveMembers } from "@/hooks/queries";
import InviteMemberModal from "../common/InviteMemberModal";
import ManageMembersModal from "../common/ManageMembersModal";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

type Props = {
  expense_group: ExpenseGroup;
};

const MembersTab = ({ expense_group }: Props) => {
  const current_user = useAuthStore((s) => s.user);
  const { mutate: removeMembers } = useRemoveMembers(expense_group.id);

  const [selectedMemberId, setSelectedMemberId] = useState<number | null>(null);
  const [showInviteMemberModal, setShowInviteMemberModal] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [showConfirmRemoveModal, setShowConfirmRemoveModal] = useState(false);
  const [error, setError] = useState("");

  const totalRatio = expense_group.members.reduce(
    (sum, m) => sum + Math.round(m.default_split_ratio * 100 * 100) / 100,
    0,
  );
  const roundedTotal = Math.round(totalRatio * 100) / 100;
  const ratioStatus =
    roundedTotal === 100 ? "exact" : roundedTotal < 100 ? "under" : "over";

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(""), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const selectedMember =
    expense_group.members.find((m) => m.user_id === selectedMemberId) ?? null;

  const isAdmin = expense_group.members.some(
    (m) => m.user_id === current_user?.id && m.role === "admin",
  );

  const getMemberFullName = (user: User | undefined) => {
    if (!user) return "";
    return `${user.firstname ?? ""} ${user.lastname ?? ""}`.trim();
  };

  const handleConfirmRemoveMember = () => {
    setShowConfirmRemoveModal(false);
    setSelectedMemberId(null);
    if (selectedMemberId) {
      removeMembers([selectedMemberId], {
        onError: () => setError("Failed to remove member. Please try again."),
      });
    }
  };

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        {/* <h2 className={styles.sectionTitle}>Members</h2> */}
        <div className={styles.sectionActions}>
          <span
            className={`${styles.ratioTotal} ${styles[`ratioTotal_${ratioStatus}`]}`}
          >
            {roundedTotal}%
          </span>
          <button
            className={styles.manageBtn}
            onClick={() => setShowManageModal(true)}
          >
            <Icon icon="ph:sliders" width={16} height={16} />
            Manage
          </button>
          {isAdmin && (
            <button
              className={styles.addBtn}
              onClick={() => setShowInviteMemberModal(true)}
            >
              <Icon icon="ph:user-plus" width={16} height={16} />
              Invite
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className={styles.errorBanner}>
          <Icon icon="ph:warning-circle" width={16} height={16} />
          {error}
        </div>
      )}

      <div className={styles.list}>
        {expense_group.members.map((member) => (
          <div key={member.user_id} className={styles.memberItem}>
            <div className={styles.memberAvatar}>
              {member.user?.username?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className={styles.memberInfo}>
              <span className={styles.memberName}>
                {getMemberFullName(member.user)}{" "}
                <span className={styles.memberUsername}>
                  @{member.user?.username}
                </span>
                {member.user_id === current_user?.id ? " (you)" : ""}
              </span>
              <span className={styles.memberMeta}>
                {Math.round(member.default_split_ratio * 100 * 100) / 100}%
                split
              </span>
            </div>
            <span
              className={`${styles.roleBadge} ${member.role === "admin" ? styles.roleAdmin : styles.roleMember}`}
            >
              {member.role}
            </span>
            {isAdmin && member.user_id !== current_user?.id && (
              <button
                className={`${styles.actionBtn} ${styles.actionDelete}`}
                onClick={() => {
                  setSelectedMemberId(member.user_id);
                  setShowConfirmRemoveModal(true);
                }}
              >
                <Icon icon="ph:x" width={14} height={14} />
              </button>
            )}
          </div>
        ))}
      </div>

      {showInviteMemberModal && (
        <InviteMemberModal
          expense_group={expense_group}
          onClose={() => setShowInviteMemberModal(false)}
        />
      )}

      {showManageModal && (
        <ManageMembersModal
          expense_group={expense_group}
          onClose={() => setShowManageModal(false)}
        />
      )}

      {showConfirmRemoveModal && selectedMember && (
        <ConfirmModal
          title="Remove member"
          message={`"${getMemberFullName(selectedMember.user)} (@${selectedMember.user?.username})" will be removed from this group.`}
          confirmLabel="Remove"
          danger
          onConfirm={handleConfirmRemoveMember}
          onCancel={() => {
            setShowConfirmRemoveModal(false);
            setSelectedMemberId(null);
          }}
        />
      )}
    </div>
  );
};

export default MembersTab;
