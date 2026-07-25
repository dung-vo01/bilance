import { useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "@iconify/react";
import {
  useCancelContactRequest,
  useContactsDetail,
  useNotifications,
  useRemoveContact,
  useRespondToContactRequest,
  useSendContactRequest,
  useSentContactRequests,
} from "@/hooks/queries";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import type { ContactDetail } from "@/types";
import styles from "./ContactsPage.module.scss";

const getFullName = (
  person: { firstname?: string | null; lastname?: string | null } | null,
  fallbackUsername: string,
) => {
  const fullName =
    `${person?.firstname ?? ""} ${person?.lastname ?? ""}`.trim();
  return fullName || fallbackUsername;
};

export const ContactsPage = () => {
  const { data: contacts = [], isLoading: contactsLoading } =
    useContactsDetail();
  const { data: notifications = [] } = useNotifications();
  const { data: sentRequests = [], isLoading: sentLoading } =
    useSentContactRequests();

  const { mutate: sendRequest, isPending: isSending } = useSendContactRequest();
  const { mutate: respond, isPending: isResponding } =
    useRespondToContactRequest();
  const { mutate: cancelRequest, isPending: isCancelling } =
    useCancelContactRequest();
  const { mutate: removeContact } = useRemoveContact();

  const [addUsername, setAddUsername] = useState("");
  const [addError, setAddError] = useState("");
  const [addSuccess, setAddSuccess] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState<ContactDetail | null>(
    null,
  );

  const incomingRequests = notifications.filter(
    (n) => n.type === "contact_request" && n.resolved_at === null,
  );

  const handleAddFriend = (e: React.FormEvent) => {
    e.preventDefault();
    setAddError("");
    setAddSuccess(false);
    sendRequest(addUsername, {
      onSuccess: () => {
        setAddSuccess(true);
        setAddUsername("");
      },
      onError: () =>
        setAddError(
          "Couldn't send that request — check the username and try again.",
        ),
    });
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Friends</h1>
          <p className={styles.subtitle}>
            Manage your contacts and friend requests
          </p>
        </div>
      </div>

      <form className={styles.addFriendBar} onSubmit={handleAddFriend}>
        <Icon icon="ph:user-plus" width={18} height={18} />
        <input
          className={styles.addFriendInput}
          value={addUsername}
          onChange={(e) => setAddUsername(e.target.value)}
          placeholder="Send a friend request by exact username..."
        />
        <button
          type="submit"
          className={styles.addFriendBtn}
          disabled={isSending || !addUsername}
        >
          {isSending ? "Sending..." : "Send request"}
        </button>
      </form>
      {addError && (
        <div className={styles.error}>
          <Icon icon="ph:warning-circle" width={16} height={16} />
          {addError}
        </div>
      )}
      {addSuccess && (
        <div className={styles.success}>
          <Icon icon="ph:check-circle" width={16} height={16} />
          Request sent.
        </div>
      )}

      {incomingRequests.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Requests</h2>
          <div className={styles.list}>
            {incomingRequests.map((n) => (
              <div key={n.id} className={styles.item}>
                <div className={styles.avatar}>
                  {(n.actor?.username?.[0] ?? "?").toUpperCase()}
                </div>
                <div className={styles.info}>
                  <span className={styles.name}>
                    {getFullName(n.actor, n.actor?.username ?? "Someone")}
                  </span>
                  <span className={styles.username}>@{n.actor?.username}</span>
                </div>
                <div className={styles.rowActions}>
                  <button
                    type="button"
                    className={styles.acceptBtn}
                    disabled={isResponding}
                    onClick={() => respond({ id: n.id, accept: true })}
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    className={styles.declineBtn}
                    disabled={isResponding}
                    onClick={() => respond({ id: n.id, accept: false })}
                  >
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {!sentLoading && sentRequests.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Sent</h2>
          <div className={styles.list}>
            {sentRequests.map((n) => (
              <div key={n.id} className={styles.item}>
                <div className={styles.avatar}>
                  {(n.recipient?.username?.[0] ?? "?").toUpperCase()}
                </div>
                <div className={styles.info}>
                  <span className={styles.name}>
                    {getFullName(
                      n.recipient ?? null,
                      n.recipient?.username ?? "Someone",
                    )}
                  </span>
                  <span className={styles.username}>
                    @{n.recipient?.username}
                  </span>
                </div>
                <div className={styles.rowActions}>
                  <button
                    type="button"
                    className={styles.cancelBtn}
                    disabled={isCancelling}
                    onClick={() => cancelRequest(n.id)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Your contacts</h2>
        {contactsLoading ? (
          <div className={styles.loading}>
            <Icon
              icon="ph:circle-notch"
              width={24}
              height={24}
              className={styles.spin}
            />
          </div>
        ) : contacts.length === 0 ? (
          <div className={styles.empty}>
            <Icon icon="ph:address-book" width={40} height={40} />
            <p>No contacts yet</p>
          </div>
        ) : (
          <div className={styles.list}>
            {contacts.map((contact) => (
              <div key={contact.id} className={styles.item}>
                <div className={styles.avatar}>
                  {contact.username[0].toUpperCase()}
                </div>
                <div className={styles.info}>
                  <span className={styles.name}>
                    {getFullName(contact, contact.username)}
                  </span>
                  <span className={styles.username}>@{contact.username}</span>
                  <span className={styles.meta}>
                    {[contact.email, contact.phone_number]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                  {contact.shared_groups.length > 0 && (
                    <span className={styles.meta}>
                      Shared groups:{" "}
                      {contact.shared_groups.map((g, i) => (
                        <span key={g.id}>
                          {i > 0 && ", "}
                          <Link
                            to={`/expense_groups/${g.id}`}
                            className={styles.groupLink}
                          >
                            {g.name ?? `Group #${g.id}`}
                          </Link>
                        </span>
                      ))}
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  className={styles.removeBtn}
                  onClick={() => setConfirmRemove(contact)}
                >
                  <Icon icon="ph:x" width={14} height={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {confirmRemove && (
        <ConfirmModal
          title="Unfriend?"
          message={`@${confirmRemove.username} will be removed from your contacts.`}
          confirmLabel="Unfriend"
          danger
          onConfirm={() => {
            removeContact(confirmRemove.id);
            setConfirmRemove(null);
          }}
          onCancel={() => setConfirmRemove(null)}
        />
      )}
    </div>
  );
};
