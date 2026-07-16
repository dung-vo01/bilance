import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { Icon } from "@iconify/react";
import { authApi } from "@/api";
import { useAuthStore } from "@/stores/authStore";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { useGuestLogin, useResendVerification } from "@/hooks/queries";
import { useSlowLoading } from "@/hooks/useSlowLoading";
import type { ApiError } from "@/types";
import styles from "./Auth.module.scss";

export const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [unverified, setUnverified] = useState(false);
  const [resent, setResent] = useState(false);

  const resetSuccess = Boolean(
    (location.state as { resetSuccess?: boolean } | null)?.resetSuccess,
  );

  const { mutate, isPending } = useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      const { user, access_token, refresh_token } = res.data.data;
      setAuth(user, access_token, refresh_token);
      navigate("/dashboard");
    },
    onError: (err: AxiosError<ApiError>) => {
      setUnverified(err.response?.status === 403);
      setError(err.response?.data?.error || "Login failed");
    },
  });

  const { mutate: resendVerification, isPending: isResending } =
    useResendVerification();
  const { mutate: guestLogin, isPending: isGuestPending } = useGuestLogin();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setUnverified(false);
    setResent(false);
    mutate(form);
  };

  const handleResend = () => {
    resendVerification(form.email, { onSuccess: () => setResent(true) });
  };

  const handleGuestLogin = () => {
    guestLogin(undefined, { onSuccess: () => navigate("/dashboard") });
  };

  const isSlow = useSlowLoading(isPending);

  return (
    <AuthLayout>
      <>
        <form onSubmit={handleSubmit} className={styles.form}>
          {resetSuccess && !error && (
            <div className={styles.success}>
              <Icon icon="ph:check-circle" width={16} height={16} />
              Password updated. Please sign in.
            </div>
          )}

          {error && (
            <div className={styles.error}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {error}
            </div>
          )}

          {unverified && (
            <button
              type="button"
              className={styles.linkBtn}
              onClick={handleResend}
              disabled={isResending || resent}
            >
              {resent
                ? "Verification email resent"
                : isResending
                  ? "Sending..."
                  : "Resend verification email"}
            </button>
          )}

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
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Password</label>
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
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>
            <Link to="/forgot-password" className={styles.forgotLink}>
              Forgot your password?
            </Link>
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
                Signing in...
              </>
            ) : (
              "Sign in"
            )}
          </button>

          {isSlow && (
            <p className={styles.slowNotice}>
              Still working - the server can take up to a minute to respond
              after sitting idle.
            </p>
          )}
        </form>

        <div className={styles.divider}>or</div>

        <button
          type="button"
          className={styles.guestBtn}
          onClick={handleGuestLogin}
          disabled={isGuestPending}
        >
          {isGuestPending ? (
            <>
              <Icon
                icon="ph:circle-notch"
                width={16}
                height={16}
                className={styles.spin}
              />
              Setting up...
            </>
          ) : (
            "Continue as Guest"
          )}
        </button>

        <p className={styles.switch}>
          No account? <Link to="/register">Create one</Link>
        </p>
      </>
    </AuthLayout>
  );
};
