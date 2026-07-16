import type { ReactNode } from "react";
import { Icon } from "@iconify/react";
import { useUIStore } from "@/stores/uiStore";
import { BilanceMark } from "@/components/ui/BilanceMark";
import { Footer } from "@/components/ui/Footer";
import styles from "@/pages/auth/Auth.module.scss";

interface Props {
  children: ReactNode;
}

export const AuthLayout = ({ children }: Props) => {
  const { theme, toggleTheme } = useUIStore();

  return (
    <div className={styles.container}>
      <button
        onClick={toggleTheme}
        className={styles.themeBtn}
        title="Toggle theme"
      >
        <Icon
          icon={theme === "light" ? "ph:moon" : "ph:sun"}
          width={20}
          height={20}
        />
      </button>

      <div className={styles.card}>
        <div className={styles.logoWrap}>
          <div className={styles.logo}>
            <BilanceMark size={40} />
            <span>
              <span className={styles.logoBi}>Bi</span>
              <span className={styles.logoLance}>lance</span>
            </span>
          </div>
          <p className={styles.tagline}>balance what you owe</p>
        </div>

        {children}
      </div>

      <Footer className={styles.pageFooter} />
    </div>
  );
};
