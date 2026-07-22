import { Icon } from "@iconify/react";
import styles from "./InviteMemberModal.module.scss";
import { SearchSelect } from "@/components/ui/SearchSelect";
import type { ContactUser, ExpenseGroup } from "@/types";
import {
  useContacts,
  useInviteMembers,
  useSendContactRequest,
} from "@/hooks/queries";
import { useState } from "react";

type InviteEntry = {
  username: string;
  default_split_ratio: number;
};

type Props = { expense_group: ExpenseGroup; onClose: () => void };

const InviteMemberModal = ({ expense_group, onClose }: Props) => {
  const { mutate: inviteMembers, isPending } = useInviteMembers(
    expense_group.id,
  );
  const { data: users = [] } = useContacts();

  const [invites, setInvites] = useState<InviteEntry[]>([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const [showAddContact, setShowAddContact] = useState(false);
  const [contactUsername, setContactUsername] = useState("");
  const [contactError, setContactError] = useState("");
  const [contactSent, setContactSent] = useState(false);
  const { mutate: sendContactRequest, isPending: isSendingRequest } =
    useSendContactRequest();

  const existingUserIds = new Set(expense_group.members.map((m) => m.user_id));
  const invitedUsernames = new Set(invites.map((i) => i.username));
  const pendingUsernames = new Set(
    expense_group.pending_invitations.map((p) => p.username),
  );

  const availableUsers = users.filter(
    (u) =>
      !existingUserIds.has(u.id) &&
      !invitedUsernames.has(u.username) &&
      !pendingUsernames.has(u.username),
  );

  const getUserOptionLabel = (user: ContactUser) => {
    let text = user.username;
    if (user.firstname || user.lastname) {
      text += ` (${[user.firstname, user.lastname].filter(Boolean).join(" ")})`;
    }
    return text;
  };

  const handleSendContactRequest = (e: React.FormEvent) => {
    e.preventDefault();
    setContactError("");
    sendContactRequest(contactUsername, {
      onSuccess: () => {
        setContactSent(true);
        setContactUsername("");
      },
      onError: () =>
        setContactError(
          "Couldn't send that request — check the username and try again.",
        ),
    });
  };

  // default_split_ratio is a decimal float (0.5 = 50%)
  const existingTotalRaw = expense_group.members.reduce(
    (sum, m) => sum + m.default_split_ratio,
    0,
  );
  const existingTotal = Math.round(existingTotalRaw * 100 * 100) / 100; // convert to %, 2 decimals
  const remaining = Math.round((100 - existingTotal) * 100) / 100;

  // new invites are stored as % strings
  const newTotalRaw = invites.reduce(
    (sum, i) => sum + i.default_split_ratio,
    0,
  );
  const newTotal = Math.round(newTotalRaw * 100 * 100) / 100;

  const ratioStatus =
    newTotal === remaining ? "exact" : newTotal < remaining ? "under" : "over";
  const ratioValid = ratioStatus !== "over";

  const addInvite = (username: string) => {
    if (!username || invitedUsernames.has(username)) return;
    setInvites((prev) => [...prev, { username, default_split_ratio: 0 }]);
  };

  const removeInvite = (username: string) => {
    setInvites((prev) => prev.filter((i) => i.username !== username));
  };

  const updateRatio = (username: string, value: string) => {
    const asDecimal = Math.round((parseFloat(value) / 100) * 10000) / 10000;
    setInvites((prev) =>
      prev.map((i) =>
        i.username === username
          ? { ...i, default_split_ratio: isNaN(asDecimal) ? 0 : asDecimal }
          : i,
      ),
    );
  };

  const distributeEqually = () => {
    if (invites.length === 0) return;
    const remainingDecimal = remaining / 100; // convert % to decimal
    const equal =
      Math.round((remainingDecimal / invites.length) * 10000) / 10000;
    const last =
      Math.round((remainingDecimal - equal * (invites.length - 1)) * 10000) /
      10000;
    setInvites((prev) =>
      prev.map((invite, i) => ({
        ...invite,
        default_split_ratio: i === invites.length - 1 ? last : equal,
      })),
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (invites.length === 0) {
      setError("Add at least one member to invite.");
      return;
    }
    if (!ratioValid) {
      setError(`New members' total cannot exceed the remaining ${remaining}%.`);
      return;
    }

    // convert % string back to decimal float for the backend
    const members = invites.map((i) => ({
      username: i.username,
      default_split_ratio: i.default_split_ratio,
    }));

    inviteMembers(
      { members },
      {
        onSuccess: () => {
          setSuccess(true);
          setTimeout(onClose, 1800);
        },
        onError: () => setError("Failed to invite members. Please try again."),
      },
    );
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>Invite members</h2>
          <button onClick={onClose} className={styles.closeBtn}>
            <Icon icon="ph:x" width={18} height={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.fields}>
            {error && (
              <div className={styles.error}>
                <Icon icon="ph:warning-circle" width={16} height={16} />
                {error}
              </div>
            )}

            {success && (
              <div className={styles.success}>
                <Icon icon="ph:check-circle" width={16} height={16} />
                Invites sent — pending acceptance.
              </div>
            )}

            {/* Existing members - display only */}
            <div className={styles.existingList}>
              <p className={styles.existingTitle}>Current members</p>
              {expense_group.members.map((m) => (
                <div key={m.user_id} className={styles.existingRow}>
                  <div className={styles.inviteAvatar}>
                    {m.user?.username?.[0]?.toUpperCase()}
                  </div>
                  <span className={styles.existingName}>
                    {m.user?.firstname || m.user?.lastname
                      ? `${m.user.firstname ?? ""} ${m.user.lastname ?? ""}`.trim()
                      : m.user?.username}
                  </span>
                  <span className={styles.existingSplit}>
                    {Math.round(m.default_split_ratio * 100 * 100) / 100}%
                  </span>
                </div>
              ))}
            </div>

            {/* Already-invited, unresolved - display only */}
            {expense_group.pending_invitations.length > 0 && (
              <div className={styles.existingList}>
                <p className={styles.existingTitle}>Pending invitations</p>
                {expense_group.pending_invitations.map((p) => (
                  <div key={p.id} className={styles.existingRow}>
                    <div className={styles.inviteAvatar}>
                      {p.username[0]?.toUpperCase()}
                    </div>
                    <span className={styles.existingName}>
                      {p.firstname || p.lastname
                        ? `${p.firstname ?? ""} ${p.lastname ?? ""}`.trim()
                        : p.username}
                    </span>
                    <span className={styles.pendingBadge}>Invited</span>
                  </div>
                ))}
              </div>
            )}

            {/* Remaining pool + status */}
            <div className={styles.ratioBar}>
              <div className={styles.ratioBarLeft}>
                <span className={styles.ratioTotal}>
                  Remaining: {remaining}%
                </span>
                {invites.length > 0 && (
                  <span
                    className={`${styles.ratioHint} ${styles[`ratioHint_${ratioStatus}`]}`}
                  >
                    {ratioStatus === "exact" && "Fully allocated ✓"}
                    {ratioStatus === "under" &&
                      `${Math.round((remaining - newTotal) * 100) / 100}% unassigned`}
                    {ratioStatus === "over" &&
                      `Exceeds by ${Math.round((newTotal - remaining) * 100) / 100}%`}
                  </span>
                )}
              </div>
              {invites.length > 0 && (
                <button
                  type="button"
                  className={styles.distributeBtn}
                  onClick={distributeEqually}
                >
                  Distribute equally
                </button>
              )}
            </div>

            {availableUsers.length > 0 && (
              <div className={styles.field}>
                <label className={styles.label}>Add member</label>
                <SearchSelect
                  value=""
                  onChange={addInvite}
                  options={availableUsers.map((u) => ({
                    value: u.username,
                    label: getUserOptionLabel(u),
                  }))}
                  placeholder="Search and select user..."
                  searchPlaceholder="Search by username or name..."
                />
              </div>
            )}

            {/* Only contacts (and shared-group members) are invitable - this
                is how you connect with someone new before you can invite them */}
            <div className={styles.addContactSection}>
              <button
                type="button"
                className={styles.addContactToggle}
                onClick={() => setShowAddContact((v) => !v)}
              >
                <Icon
                  icon={showAddContact ? "ph:caret-down" : "ph:caret-right"}
                  width={14}
                  height={14}
                />
                Can't find them? Send a contact request
              </button>

              {showAddContact && (
                <div className={styles.addContactForm}>
                  {contactError && (
                    <div className={styles.error}>
                      <Icon icon="ph:warning-circle" width={16} height={16} />
                      {contactError}
                    </div>
                  )}
                  {contactSent ? (
                    <div className={styles.success}>
                      <Icon icon="ph:check-circle" width={16} height={16} />
                      Request sent — once they accept, you can invite them.
                    </div>
                  ) : (
                    <div className={styles.addContactRow}>
                      <input
                        type="text"
                        className={styles.addContactInput}
                        value={contactUsername}
                        onChange={(e) => setContactUsername(e.target.value)}
                        placeholder="Their exact username"
                      />
                      <button
                        type="button"
                        className={styles.sendRequestBtn}
                        onClick={handleSendContactRequest}
                        disabled={isSendingRequest || !contactUsername}
                      >
                        {isSendingRequest ? "Sending..." : "Send request"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* New invites */}
            {invites.length > 0 && (
              <div className={styles.inviteList}>
                {invites.map((invite) => {
                  const user = users.find(
                    (u) => u.username === invite.username,
                  );
                  return (
                    <div key={invite.username} className={styles.inviteRow}>
                      <div className={styles.inviteAvatar}>
                        {invite.username[0].toUpperCase()}
                      </div>
                      <div className={styles.inviteInfo}>
                        <span className={styles.inviteName}>
                          {user?.firstname || user?.lastname
                            ? `${user.firstname ?? ""} ${user.lastname ?? ""}`.trim()
                            : invite.username}
                        </span>
                        <span className={styles.inviteUsername}>
                          @{invite.username}
                        </span>
                      </div>
                      <div className={styles.shareInputWrap}>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="0.01"
                          className={styles.shareInput}
                          value={
                            Math.round(invite.default_split_ratio * 100 * 100) /
                            100
                          }
                          onChange={(e) =>
                            updateRatio(invite.username, e.target.value)
                          }
                        />
                        <span className={styles.shareSuffix}>%</span>
                      </div>
                      <button
                        type="button"
                        className={styles.removeBtn}
                        onClick={() => removeInvite(invite.username)}
                      >
                        <Icon icon="ph:x" width={14} height={14} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className={styles.formActions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelBtn}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={
                isPending || success || invites.length === 0 || !ratioValid
              }
            >
              Invite {invites.length > 0 ? `(${invites.length})` : ""}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InviteMemberModal;
