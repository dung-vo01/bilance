import axios from "axios";
import { navigateTo } from "@/utils/navigate";
import { useAuthStore } from "@/stores/authStore";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const stored = localStorage.getItem("bilance-auth");
  const parsed = stored ? JSON.parse(stored) : null;
  const token = parsed?.state?.accessToken;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // stop immediately if refresh itself fails
    if (original.url?.includes("/auth/refresh")) {
      // when auth fails
      useAuthStore.getState().logout();
      navigateTo("/login");
      return Promise.reject(error);
    }

    // stop if already retried once
    if (original._retry) {
      // when auth fails
      useAuthStore.getState().logout();
      navigateTo("/login");
      return Promise.reject(error);
    }

    if (error.response?.status === 401) {
      original._retry = true;

      try {
        const stored = localStorage.getItem("bilance-auth");
        const refreshToken = stored
          ? JSON.parse(stored)?.state?.refreshToken
          : null;

        if (!refreshToken) {
          // when auth fails
          useAuthStore.getState().logout();
          navigateTo("/login");
          return Promise.reject(error);
        }

        const { data } = await axios.post("/api/auth/refresh", null, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });

        // update zustand store
        const current = JSON.parse(
          localStorage.getItem("bilance-auth") || "{}",
        );
        current.state.accessToken = data.data.access_token;
        current.state.refreshToken = data.data.refresh_token;
        localStorage.setItem("bilance-auth", JSON.stringify(current));

        original.headers.Authorization = `Bearer ${data.data.access_token}`;
        return api(original);
      } catch {
        // when auth fails
        useAuthStore.getState().logout();
        navigateTo("/login");
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
