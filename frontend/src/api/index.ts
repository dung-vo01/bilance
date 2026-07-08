import api from "./client";
import type {
  AuthTokens,
  User,
  ExpenseGroup,
  Expense,
  Category,
  Settlement,
  Notification,
  UpdateUserPayload,
  UpdateCategoryPayload,
  UpdateExpenseGroupPayload,
  ExpenseGroupMember,
  NewCategoryPayload,
  NewExpenseGroupPayload,
  NewExpensePayload,
  UpdateExpensePayload,
  NewUserPayload,
  ExpenseListParams,
  PaginatedExpenses,
} from "@/types";

//--------------------------------------------------------------------------------
// Auth
//--------------------------------------------------------------------------------
export const authApi = {
  register: (data: {
    username: string;
    email: string;
    password: string;
    firstname?: string;
    lastname?: string;
  }) => api.post<{ data: AuthTokens }>("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    api.post<{ data: AuthTokens }>("/auth/login", data),

  me: () => api.get<{ data: User }>("/auth/me"),
};

//--------------------------------------------------------------------------------
// Users
//--------------------------------------------------------------------------------
export const usersApi = {
  getAll: (params?: { search_kw?: string; roles?: string[] }) =>
    api.get<{ data: User[] }>("/users", {
      params: {
        search_kw: params?.search_kw,
        roles: params?.roles?.join(","),
      },
    }),

  getOne: (id: number) => api.get<{ data: User }>(`/users/${id}`),

  create: (data: NewUserPayload) => api.post<{ data: User }>("/users", data),

  update: (id: number, data: UpdateUserPayload) =>
    api.patch<{ data: User }>(`/users/${id}`, data),

  delete: (id: number) => api.delete(`/users/${id}`),
};

//--------------------------------------------------------------------------------
// Categories
//--------------------------------------------------------------------------------
export const categoriesApi = {
  getAll: (params?: { expense_group_id?: number }) =>
    api.get<{ data: Category[] }>("/categories", { params }),

  create: (data: NewCategoryPayload) =>
    api.post<{ data: Category }>("/categories", data),

  update: (id: number, data: UpdateCategoryPayload) =>
    api.patch<{ data: Category }>(`/categories/${id}`, data),

  delete: (id: number) => api.delete(`/categories/${id}`),
};

//--------------------------------------------------------------------------------
// Expense Groups
//--------------------------------------------------------------------------------
export const expenseGroupsApi = {
  getAll: () => api.get<{ data: ExpenseGroup[] }>("/expense-groups"),

  getOne: (id: number) =>
    api.get<{ data: ExpenseGroup }>(`/expense-groups/${id}`),

  create: (data: NewExpenseGroupPayload) =>
    api.post<{ data: ExpenseGroup }>("/expense-groups", data),

  update: (id: number, data: UpdateExpenseGroupPayload) =>
    api.patch<{ data: ExpenseGroup }>(`/expense-groups/${id}`, data),

  delete: (id: number) => api.delete(`/expense-groups/${id}`),

  invite: (id: number, data: { members: { username: string }[] }) =>
    api.post<{ data: Notification[] }>(`/expense-groups/${id}/invite`, data),

  leave: (id: number) => api.post(`/expense-groups/${id}/leave`),

  updateMember: (
    groupId: number,
    userId: number,
    data: { default_split_ratio?: number; role?: string },
  ) =>
    api.patch<{ data: ExpenseGroupMember }>(
      `/expense-groups/${groupId}/members/${userId}`,
      data,
    ),

  bulkUpdateMembers: (
    groupId: number,
    members: { user_id: number; default_split_ratio?: number; role?: string }[],
  ) =>
    api.patch<{ data: ExpenseGroupMember[] }>(
      `/expense-groups/${groupId}/members`,
      { members },
    ),

  removeMembers: (id: number, member_ids: number[]) =>
    api.delete(`/expense-groups/${id}/members`, {
      params: { member_ids: member_ids.join(",") },
    }),

  getSettlement: (id: number) =>
    api.get<{ data: Settlement }>(`/expense-groups/${id}/settlement`),
};

//--------------------------------------------------------------------------------
// Expenses
//--------------------------------------------------------------------------------
export const expensesApi = {
  getAll: (params?: { expense_group_id?: number }) =>
    api.get<{ data: Expense[] }>("/expenses", { params }),

  getPaginated: (params: ExpenseListParams) =>
    api.get<{ data: PaginatedExpenses }>("/expenses", { params }),

  getPayees: (expense_group_id: number) =>
    api.get<{ data: User[] }>("/expenses/payees", {
      params: { expense_group_id },
    }),

  create: (data: NewExpensePayload) =>
    api.post<{ data: Expense }>("/expenses", data),

  update: (id: number, data: UpdateExpensePayload) =>
    api.patch<{ data: Expense }>(`/expenses/${id}`, data),

  delete: (id: number) => api.delete(`/expenses/${id}`),
};

//--------------------------------------------------------------------------------
// Notifications
//--------------------------------------------------------------------------------
export const notificationsApi = {
  getAll: () => api.get<{ data: Notification[] }>("/notifications"),

  markRead: (id: number) =>
    api.post<{ data: { message: string } }>(`/notifications/${id}/read`),

  respondInvitation: (id: number, accept: boolean) =>
    api.post<{ data: { message: string } }>(
      `/notifications/invitations/${id}/respond`,
      { accept },
    ),
};
