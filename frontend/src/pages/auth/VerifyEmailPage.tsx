import { Link, useParams } from "react-router-dom";
import { Icon } from "@iconify/react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { useVerifyEmail } from "@/hooks/queries";
import styles from "./Auth.module.scss";

export const VerifyEmailPage = () => {
  const { token } = useParams<{ token: string }>();
  const { isPending, isSuccess, isError } = useVerifyEmail(token);

  return (
    <AuthLayout>
      <div className={styles.centeredState}>
        {isPending && (
          <>
            <Icon
              icon="ph:circle-notch"
              width={32}
              height={32}
              className={styles.spin}
            />
            <p className={styles.message}>Verifying your email...</p>
          </>
        )}

        {isSuccess && (
          <>
            <div className={styles.success}>
              <Icon icon="ph:check-circle" width={16} height={16} />
              Your email has been verified.
            </div>
            <p className={styles.switch}>
              <Link to="/login">Sign in</Link>
            </p>
          </>
        )}

        {isError && (
          <>
            <div className={styles.error}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              This link is invalid or has expired.
            </div>
            <p className={styles.switch}>
              <Link to="/login">Back to sign in</Link>
            </p>
          </>
        )}
      </div>
    </AuthLayout>
  );
};
