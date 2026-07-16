import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Icon } from "@iconify/react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { useResendVerification } from "@/hooks/queries";
import styles from "./Auth.module.scss";

export const CheckEmailPage = () => {
  const location = useLocation();
  const email = (location.state as { email?: string } | null)?.email;
  const [resent, setResent] = useState(false);
  const { mutate, isPending } = useResendVerification();

  const handleResend = () => {
    if (!email) return;
    mutate(email, { onSuccess: () => setResent(true) });
  };

  return (
    <AuthLayout>
      <div className={styles.centeredState}>
        <Icon icon="ph:envelope-simple-open" width={40} height={40} />
        <p className={styles.message}>
          {email ? (
            <>
              We sent a verification link to <strong>{email}</strong>. Click it
              to activate your account.
            </>
          ) : (
            "We sent a verification link to your email. Click it to activate your account."
          )}
        </p>

        {email && (
          <button
            type="button"
            className={styles.linkBtn}
            onClick={handleResend}
            disabled={isPending || resent}
          >
            {resent
              ? "Email resent"
              : isPending
                ? "Sending..."
                : "Resend email"}
          </button>
        )}

        <p className={styles.switch}>
          <Link to="/login">Back to sign in</Link>
        </p>
      </div>
    </AuthLayout>
  );
};
