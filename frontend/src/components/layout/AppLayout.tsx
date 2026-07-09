import { useEffect, useRef } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { Icon } from "@iconify/react";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { NotificationBell } from "./NotificationBell";
import { BilanceMark } from "@/components/ui/BilanceMark";
import { Footer } from "@/components/ui/Footer";
import styles from "./AppLayout.module.scss";

const DESKTOP_BREAKPOINT = 1024;

export const AppLayout = () => {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, setSidebarOpen, toggleSidebar, theme, toggleTheme } =
    useUIStore();
  const navigate = useNavigate();
  const wasDesktop = useRef(window.innerWidth >= DESKTOP_BREAKPOINT);

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

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { to: "/dashboard", label: "Dashboard", icon: "ph:house" },
    { to: "/expenses", label: "Expenses", icon: "ph:receipt" },
    { to: "/expense_groups", label: "Groups", icon: "ph:users-three" },
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
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};
