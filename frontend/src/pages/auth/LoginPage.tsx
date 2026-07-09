import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { Icon } from "@iconify/react";
import { authApi } from "@/api";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { BilanceMark } from "@/components/ui/BilanceMark";
import { Footer } from "@/components/ui/Footer";
import { useSlowLoading } from "@/hooks/useSlowLoading";
import type { ApiError } from "@/types";
import styles from "./Auth.module.scss";

export const LoginPage = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const { theme, toggleTheme } = useUIStore();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  const { mutate, isPending } = useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      const { user, access_token, refresh_token } = res.data.data;
      setAuth(user, access_token, refresh_token);
      navigate("/dashboard");
    },
    onError: (err: AxiosError<ApiError>) => {
      setError(err.response?.data?.error || "Login failed");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    mutate(form);
  };

  const isSlow = useSlowLoading(isPending);

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

        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.error}>
              <Icon icon="ph:warning-circle" width={16} height={16} />
              {error}
            </div>
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

        <p className={styles.switch}>
          No account? <Link to="/register">Create one</Link>
        </p>
      </div>

      <Footer className={styles.pageFooter} />
    </div>
  );
};
