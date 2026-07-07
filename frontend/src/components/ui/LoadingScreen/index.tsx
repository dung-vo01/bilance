import { Icon } from "@iconify/react";
import { BilanceMark } from "@/components/ui/BilanceMark";
import styles from "./LoadingScreen.module.scss";

const LoadingScreen = () => {
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
    </div>
  );
};

export default LoadingScreen;
