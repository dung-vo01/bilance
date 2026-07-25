import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { setNavigate } from "@/utils/navigate";
import { ProtectedRoute, PublicRoute } from "@/components/AuthGuard";
import { AppLayout } from "@/components/layout/AppLayout";

import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { CheckEmailPage } from "@/pages/auth/CheckEmailPage";
import { VerifyEmailPage } from "@/pages/auth/VerifyEmailPage";
import { ForgotPasswordPage } from "@/pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/auth/ResetPasswordPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { ExpensesPage } from "@/pages/expenses/ExpensesPage";
import { ExpenseGroupsPage } from "@/pages/expenseGroups/ExpenseGroupsPage";
import { ExpenseGroupDetailPage } from "@/pages/expenseGroups/ExpenseGroupDetailPage";
import { ProfilePage } from "@/pages/profile/ProfilePage";
import { UsersPage } from "@/pages/users/UsersPage";
import { ContactsPage } from "@/pages/contacts/ContactsPage";

export const AppRouter = () => {
  const navigate = useNavigate();

  useEffect(() => {
    setNavigate(navigate);
  }, [navigate]);

  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/expenses" element={<ExpensesPage />} />
          <Route path="/expense_groups" element={<ExpenseGroupsPage />} />
          <Route
            path="/expense_groups/:id"
            element={<ExpenseGroupDetailPage />}
          />
          <Route path="/contacts" element={<ContactsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/users" element={<UsersPage />} />
        </Route>
      </Route>

      <Route path="/check-email" element={<CheckEmailPage />} />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};
