import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { AxiosError } from "axios";
import { Icon } from "@iconify/react";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { useResetPassword } from "@/hooks/queries";
import type { ApiError } from "@/types";
import styles from "./Auth.module.scss";

export const ResetPasswordPage = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const { mutate, isPending } = useResetPassword();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (!token) {
      setError("Invalid reset link");
      return;
    }

    mutate(
      { token, new_password: password },
      {
        onSuccess: () =>
          navigate("/login", {
            state: { resetSuccess: true },
          }),
        onError: (err: unknown) => {
          const axiosErr = err as AxiosError<ApiError>;
          setError(axiosErr.response?.data?.error || "Reset failed");
        },
      },
    );
  };

  return (
    <AuthLayout>
      <>
        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.error}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {error}
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label}>New password</label>
            <div className={styles.inputWrap}>
              <Icon
                icon="ph:lock"
                className={styles.inputIcon}
                width={16}
                height={16}
              />
              <input
                type="password"
                className={styles.input}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Confirm password</label>
            <div className={styles.inputWrap}>
              <Icon
                icon="ph:lock"
                className={styles.inputIcon}
                width={16}
                height={16}
              />
              <input
                type="password"
                className={styles.input}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
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
                Resetting...
              </>
            ) : (
              "Reset password"
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
