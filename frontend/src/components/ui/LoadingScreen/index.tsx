import { Icon } from "@iconify/react";
import { BilanceMark } from "@/components/ui/BilanceMark";
import { useSlowLoading } from "@/hooks/useSlowLoading";
import styles from "./LoadingScreen.module.scss";

const LoadingScreen = () => {
  const isSlow = useSlowLoading(true);

  return (
    <div className={styles.container}>
      <div className={styles.logo}>
        <BilanceMark size={32} />
        <span>
          <span className={styles.logoBi}>Bi</span>
          <span className={styles.logoLance}>lance</span>
        </span>
      </div>
      <Icon
        icon="ph:circle-notch"
        width={24}
        height={24}
        className={styles.spinner}
      />
      {isSlow && (
        <p className={styles.slowNotice}>
          Still waking up - the server can take up to a minute to respond after
          sitting idle.
        </p>
      )}
    </div>
  );
};

export default LoadingScreen;
