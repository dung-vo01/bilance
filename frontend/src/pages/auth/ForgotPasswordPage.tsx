import { useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "@iconify/react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { useForgotPassword } from "@/hooks/queries";
import styles from "./Auth.module.scss";

export const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("");
  const { mutate, isPending, isSuccess } = useForgotPassword();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutate(email);
  };

  if (isSuccess) {
    return (
      <AuthLayout>
        <div className={styles.centeredState}>
          <div className={styles.success}>
            <Icon icon="ph:check-circle" width={16} height={16} />
            If that email is registered, a reset link has been sent.
          </div>
          <p className={styles.switch}>
            <Link to="/login">Back to sign in</Link>
          </p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <>
        <p className={styles.intro}>
          Enter your email and we'll send you a link to reset your password.
        </p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label className={styles.label}>Email</label>
            <div className={styles.inputWrap}>
              <Icon
                icon="ph:envelope"
                className={styles.inputIcon}
                width={16}
                height={16}
              />
              <input
                type="email"
                className={styles.input}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <button type="submit" className={styles.btn} disabled={isPending}>
            {isPending ? (
              <>
                <Icon
                  icon="ph:circle-notch"
                  width={16}
                  height={16}
                  className={styles.spin}
                />
                Sending...
              </>
            ) : (
              "Send reset link"
            )}
          </button>
        </form>

        <p className={styles.switch}>
          <Link to="/login">Back to sign in</Link>
        </p>
      </>
    </AuthLayout>
  );
};
