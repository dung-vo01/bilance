import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AppRouter } from "./AppRouter";
import { useAuthStore } from "./stores/authStore";
import { useMe } from "./hooks/queries";
import { useEffect } from "react";
import LoadingScreen from "./components/ui/LoadingScreen";
import { queryClient } from "./queryClient";

const AuthSync = () => {
  const updateUser = useAuthStore((s) => s.updateUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { data: user, isLoading } = useMe();

  useEffect(() => {
    if (user) updateUser(user);
  }, [user, updateUser]);

  if (isAuthenticated && isLoading) return <LoadingScreen />;

  return <AppRouter />;
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthSync />
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
