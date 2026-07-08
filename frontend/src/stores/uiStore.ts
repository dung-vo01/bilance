import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark";

interface UIState {
  sidebarOpen: boolean;
  theme: Theme;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const getDefaultSidebarOpen = () =>
  typeof window !== "undefined" ? window.innerWidth >= 1024 : true;

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      sidebarOpen: getDefaultSidebarOpen(),
      theme: "light",
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      toggleTheme: () => {
        const next = get().theme === "light" ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", next);
        set({ theme: next });
      },
      setTheme: (theme) => {
        document.documentElement.setAttribute("data-theme", theme);
        set({ theme });
      },
    }),
    {
      name: "bilance-ui",
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        // apply saved theme on page load
        if (state?.theme) {
          document.documentElement.setAttribute("data-theme", state.theme);
        }
      },
    },
  ),
);
