import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Icon } from "@iconify/react";
import { authApi } from "@/api";
import { useAuthStore } from "@/stores/authStore";
import { useUIStore } from "@/stores/uiStore";
import { BilanceMark } from "@/components/ui/BilanceMark";
import styles from "./Auth.module.scss";

export const RegisterPage = () => {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const { theme, toggleTheme } = useUIStore();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    firstname: "",
    lastname: "",
    phone_number: "",
  });
  const [error, setError] = useState("");

  const { mutate, isPending } = useMutation({
    mutationFn: authApi.register,
    onSuccess: (res) => {
      const { user, access_token, refresh_token } = res.data.data;
      setAuth(user, access_token, refresh_token);
      navigate("/dashboard");
    },
    onError: (err: any) => {
      setError(err.response?.data?.error || "Registration failed");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    mutate(form);
  };

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

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>First name</label>
              <input
                className={styles.input}
                value={form.firstname}
                onChange={(e) =>
                  setForm({ ...form, firstname: e.target.value })
                }
                placeholder="John"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Last name</label>
              <input
                className={styles.input}
                value={form.lastname}
                onChange={(e) => setForm({ ...form, lastname: e.target.value })}
                placeholder="Doe"
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Username</label>
            <div className={styles.inputWrap}>
              <Icon
                icon="ph:at"
                className={styles.inputIcon}
                width={16}
                height={16}
              />
              <input
                className={styles.input}
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                placeholder="john.doe"
                required
              />
            </div>
          </div>

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
                placeholder="john.doe@gmail.com"
                required
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Phone number</label>
            <div className={styles.inputWrap}>
              <Icon
                icon="ph:phone"
                className={styles.inputIcon}
                width={16}
                height={16}
              />
              <input
                type="text"
                className={styles.input}
                value={form.phone_number}
                onChange={(e) =>
                  setForm({ ...form, phone_number: e.target.value })
                }
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
                Creating account...
              </>
            ) : (
              "Create account"
            )}
          </button>
        </form>

        <p className={styles.switch}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
};
