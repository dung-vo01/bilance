import { useEffect, useRef, useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { useGuestLogout } from "@/hooks/queries";
import { NotificationBell } from "./NotificationBell";
import { BilanceMark } from "@/components/ui/BilanceMark";
import { ConfirmModal } from "@/components/ui/ConfirmModal";
import { Footer } from "@/components/ui/Footer";
import styles from "./AppLayout.module.scss";

const DESKTOP_BREAKPOINT = 1024;

export const AppLayout = () => {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen, toggleSidebar, theme, toggleTheme } =
    useUIStore();
  const navigate = useNavigate();
  const wasDesktop = useRef(window.innerWidth >= DESKTOP_BREAKPOINT);
  const [showGuestLogoutConfirm, setShowGuestLogoutConfirm] = useState(false);
  const { mutate: guestLogout } = useGuestLogout();

  useEffect(() => {
    const handleResize = () => {
      const isDesktop = window.innerWidth >= DESKTOP_BREAKPOINT;
      if (isDesktop !== wasDesktop.current) {
        wasDesktop.current = isDesktop;
        setSidebarOpen(isDesktop);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [setSidebarOpen]);

  const finishLogout = () => {
    logout();
    navigate("/login");
  };

  const handleLogout = () => {
    if (user?.is_guest) {
      setShowGuestLogoutConfirm(true);
      return;
    }
    finishLogout();
  };

  const confirmGuestLogout = () => {
    setShowGuestLogoutConfirm(false);
    // Best-effort: the account gets swept by the TTL cleanup either way,
    // so a failed request here shouldn't block signing the user out locally.
    guestLogout(undefined, { onSettled: finishLogout });
  };

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: "ph:house" },
    { to: "/expenses", label: "Expenses", icon: "ph:receipt" },
    { to: "/expense_groups", label: "Groups", icon: "ph:users-three" },
    { to: "/contacts", label: "Friends", icon: "ph:address-book" },
    { to: "/profile", label: "Profile", icon: "ph:user" },
    ...(user?.role === "admin"
      ? [{ to: "/users", label: "Users", icon: "ph:users" }]
      : []),
  ];

  return (
    <div
      className={`${styles.layout} ${sidebarOpen ? styles.sidebarOpen : ""}`}
    >
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTop}>
          <div className={styles.logo}>
            <BilanceMark size={28} />
            <span>
              <span className={styles.logoBi}>Bi</span>
              <span className={styles.logoLance}>lance</span>
            </span>
          </div>

          <nav className={styles.nav}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
                }
              >
                <Icon icon={item.icon} width={20} height={20} />
                <span className={styles.navLabel}>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className={styles.sidebarBottom}>
          <div className={styles.userInfo}>
            <div className={styles.avatar}>
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div className={styles.userDetails}>
              <span className={styles.firstName}>{user?.firstname}</span>
              <span className={styles.userName}>@{user?.username}</span>
            </div>
            <button
              onClick={handleLogout}
              className={styles.iconBtn}
              title="Sign out"
            >
              <Icon icon="ph:sign-out" width={18} height={18} />
            </button>
          </div>

          <Footer />
        </div>
      </aside>

      <div className={styles.overlay} onClick={toggleSidebar} />

      <div className={styles.main}>
        <header className={styles.header}>
          <button onClick={toggleSidebar} className={styles.menuBtn}>
            <Icon icon="ph:list" width={22} height={22} />
          </button>
          <div className={styles.headerRight}>
            <NotificationBell />
            <button
              onClick={toggleTheme}
              className={styles.menuBtn}
              title="Toggle theme"
            >
              <Icon
                icon={theme === "light" ? "ph:moon" : "ph:sun"}
                width={20}
                height={20}
              />
            </button>
          </div>
        </header>
        {user?.is_guest && (
          <div className={styles.guestBanner}>
            <Icon icon="ph:info" width={16} height={16} />
            You're exploring as a guest - this data is deleted when you sign
            out, or automatically after 24 hours.
          </div>
        )}
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>

      {showGuestLogoutConfirm && (
        <ConfirmModal
          title="Sign out and delete guest data?"
          message="This will permanently delete your guest account and everything in it - expenses, groups, all of it. This can't be undone."
          confirmLabel="Sign out & delete"
          danger
          onConfirm={confirmGuestLogout}
          onCancel={() => setShowGuestLogoutConfirm(false)}
        />
      )}
    </div>
  );
};
