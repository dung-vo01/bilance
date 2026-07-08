import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Icon } from "@iconify/react";
import styles from "./NotificationBell.module.scss";
import {
  useMarkNotificationRead,
  useNotifications,
  useRespondToInvitation,
} from "@/hooks/queries";
import type { Notification, NotificationPersonRef } from "@/types";

const getDisplayName = (person?: NotificationPersonRef | null) => {
  if (!person) return "Someone";
  const fullName = `${person.firstname ?? ""} ${person.lastname ?? ""}`.trim();
  return fullName ? `${fullName} (${person.username})` : person.username;
};

const formatTimestamp = (isoString: string) =>
  new Date(isoString).toLocaleString("en-FI", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export const NotificationBell = () => {
  const [open, setOpen] = useState(false);
  const [panelPos, setPanelPos] = useState({ top: 0, right: 0 });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const isMobile = window.innerWidth < 768;

  const { data: notifications = [] } = useNotifications();
  const { mutate: markRead } = useMarkNotificationRead();
  const { mutate: respond, isPending: isResponding } = useRespondToInvitation();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      // On mobile, the full-screen backdrop's own onClick closes the panel
      // instead. Closing here on mousedown would unmount the backdrop before
      // iOS Safari's delayed synthetic click fires, letting that click fall
      // through onto whatever element ends up underneath.
      if (isMobile) return;
      if (
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node) &&
        panelRef.current &&
        !panelRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleScroll = () => updatePosition();
    window.addEventListener("scroll", handleScroll, true);
    return () => window.removeEventListener("scroll", handleScroll, true);
  }, [open]);

  const updatePosition = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPanelPos({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      });
    }
  };

  const handleToggle = () => {
    updatePosition();
    setOpen((prev) => !prev);
  };

  const renderItem = (n: Notification) => {
    const groupName = n.expense_group_name ?? `Group #${n.expense_group_id}`;
    const isPendingInvite =
      n.type === "group_invitation" && n.resolved_at === null;

    if (isPendingInvite) {
      return (
        <div key={n.id} className={styles.item}>
          <div className={styles.itemAvatar}>
            {(n.actor?.username?.[0] ?? "?").toUpperCase()}
          </div>
          <div className={styles.itemBody}>
            <p className={styles.itemText}>
              <strong>{getDisplayName(n.actor)}</strong> invited you to{" "}
              <strong>{groupName}</strong>
            </p>
            <span className={styles.itemTime}>{formatTimestamp(n.created_at)}</span>
            <div className={styles.itemActions}>
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
        </div>
      );
    }

    const statusText =
      n.type === "invitation_accepted"
        ? `${getDisplayName(n.actor)} accepted the invitation to ${groupName}.`
        : n.type === "invitation_declined"
          ? `${getDisplayName(n.actor)} declined the invitation to ${groupName}.`
          : n.type === "member_removed"
            ? n.payload?.removed_user_id != null
              ? `${getDisplayName(n.actor)} removed ${n.payload.removed_user ? getDisplayName(n.payload.removed_user) : "a member"} from ${groupName}.`
              : `${getDisplayName(n.actor)} removed you from ${groupName}.`
            : n.type === "member_left"
              ? `${getDisplayName(n.actor)} left ${groupName}.`
              : n.type === "members_invited"
                ? `${getDisplayName(n.actor)} invited ${(n.payload?.invited_users ?? []).map(getDisplayName).join(", ") || "someone"} to ${groupName}.`
                : `${getDisplayName(n.actor)} sent a notification.`;

    return (
      <div key={n.id} className={styles.item}>
        <div className={styles.itemAvatar}>
          {(n.actor?.username?.[0] ?? "?").toUpperCase()}
        </div>
        <div className={styles.itemBody}>
          <p className={styles.itemText}>{statusText}</p>
          <span className={styles.itemTime}>{formatTimestamp(n.created_at)}</span>
        </div>
        <button
          type="button"
          className={styles.dismissBtn}
          onClick={() => markRead(n.id)}
          title="Dismiss"
        >
          <Icon icon="ph:x" width={14} height={14} />
        </button>
      </div>
    );
  };

  const panel = open ? (
    <>
      {isMobile && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            zIndex: 999,
          }}
          onClick={() => setOpen(false)}
        />
      )}
      <div
        className={styles.panel}
        ref={panelRef}
        style={
          isMobile
            ? undefined
            : {
                position: "fixed",
                top: panelPos.top,
                right: panelPos.right,
                zIndex: 1000,
              }
        }
      >
        <div className={styles.panelHeader}>Notifications</div>
        <div className={styles.list}>
          {notifications.length === 0 ? (
            <div className={styles.empty}>No notifications</div>
          ) : (
            notifications.map(renderItem)
          )}
        </div>
      </div>
    </>
  ) : null;

  return (
    <div className={styles.wrapper}>
      <button
        ref={triggerRef}
        type="button"
        className={styles.bellBtn}
        onClick={handleToggle}
        title="Notifications"
      >
        <Icon icon="ph:bell" width={20} height={20} />
        {notifications.length > 0 && (
          <span className={styles.badge}>
            {notifications.length > 9 ? "9+" : notifications.length}
          </span>
        )}
      </button>
      {createPortal(panel, document.body)}
    </div>
  );
};
