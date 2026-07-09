import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import {
  authApi,
  usersApi,
  expenseGroupsApi,
  expensesApi,
  categoriesApi,
  notificationsApi,
} from "@/api";
import {
  Category,
  Expense,
  ExpenseGroup,
  ExpenseGroupMember,
  ExpenseListParams,
  Notification,
  UpdateCategoryPayload,
  UpdateExpenseGroupPayload,
  UpdateExpensePayload,
  UpdateUserPayload,
} from "@/types";
import { useAuthStore } from "@/stores/authStore";

// Query keys
export const queryKeys = {
  me: ["me"] as const,
  users: (params?: object) => ["users", params] as const,
  user: (id: number) => ["users", id] as const,
  categories: (params?: object) => ["categories", params] as const,
  expense_groups: ["expense_groups"] as const,
  expense_group: (id: number) => ["expense_groups", id] as const,
  settlement: (id: number) => ["expense_groups", id, "settlement"] as const,
  expenses: (params?: object) => ["expenses", params] as const,
  expensePayees: (expenseGroupId: number) =>
    ["expenses", "payees", expenseGroupId] as const,
  notifications: ["notifications"] as const,
};

//helpers
const removeMembers = (existing: ExpenseGroupMember[], user_ids: number[]) => {
  return existing.filter((user) => !user_ids.includes(user.user_id));
};

//--------------------------------------------------------------------------------
// Auth
//--------------------------------------------------------------------------------
export const useLogin = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      authApi.login(data),
    onSuccess: (res) => {
      const loginData = res.data.data;
      qc.setQueryData(queryKeys.me, loginData.user);
    },
  });
};

export const useMe = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => authApi.me().then((r) => r.data.data),
    enabled: isAuthenticated,
  });
};

//--------------------------------------------------------------------------------
// Users
//--------------------------------------------------------------------------------
export const useUsers = (params?: { search_kw?: string; roles?: string[] }) =>
  useQuery({
    queryKey: queryKeys.users(params),
    queryFn: () => usersApi.getAll(params).then((r) => r.data.data),
  });

export const useUser = (id: number) =>
  useQuery({
    queryKey: queryKeys.user(id),
    queryFn: () => usersApi.getOne(id).then((r) => r.data.data),
  });

export const useCreateUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: usersApi.create,
    onSuccess: (res) => {
      const created = res.data.data;
      qc.setQueryData(queryKeys.user(created.id), created);

      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });
};

export const useUpdateUser = () => {
  const qc = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserPayload }) =>
      usersApi.update(id, data),
    onSuccess: (res, { id }) => {
      const updated = res.data.data;
      if (id === currentUser?.id) {
        qc.setQueryData(queryKeys.me, updated);
      }

      qc.setQueryData(queryKeys.user(id), updated);

      // qc.setQueryData(queryKeys.users(), (old: User[] | undefined) =>
      //   old?.map((u) => (u.id === id ? updated : u)),
      // );

      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });
};

export const useDeleteUser = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: usersApi.delete,
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: queryKeys.user(id) });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });
};

//--------------------------------------------------------------------------------
// Categories
//--------------------------------------------------------------------------------
export const useCategories = (params?: { expense_group_id?: number }) =>
  useQuery({
    queryKey: queryKeys.categories(params),
    queryFn: () => categoriesApi.getAll(params).then((r) => r.data.data),
  });

export const useCreateCategory = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: (res) => {
      const created = res.data.data;
      const key = queryKeys.categories(
        created.expense_group_id
          ? { expense_group_id: created.expense_group_id }
          : undefined,
      );

      qc.setQueryData(key, (old: Category[] | undefined) =>
        old ? [...old, created] : [created],
      );
    },
  });
};

export const useUpdateCategory = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateCategoryPayload }) =>
      categoriesApi.update(id, data),
    onSuccess: (res) => {
      const updated = res.data.data;
      const key = queryKeys.categories(
        updated.expense_group_id
          ? { expense_group_id: updated.expense_group_id }
          : undefined,
      );

      qc.setQueryData(key, (old: Category[] | undefined) =>
        old?.map((c) => (c.id === updated.id ? updated : c)),
      );
    },
  });
};

export const useDeleteCategory = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: number; expense_group_id?: number }) =>
      categoriesApi.delete(id),
    onSuccess: (_, { id, expense_group_id }) => {
      const key = queryKeys.categories(
        expense_group_id ? { expense_group_id } : undefined,
      );

      qc.setQueryData(key, (old: Category[] | undefined) =>
        old?.filter((c) => c.id !== id),
      );
    },
  });
};

//--------------------------------------------------------------------------------
// Expense Groups
//--------------------------------------------------------------------------------
export const useExpenseGroups = () =>
  useQuery({
    queryKey: queryKeys.expense_groups,
    queryFn: () => expenseGroupsApi.getAll().then((r) => r.data.data),
  });

export const useExpenseGroup = (id: number) =>
  useQuery({
    queryKey: queryKeys.expense_group(id),
    queryFn: () => expenseGroupsApi.getOne(id).then((r) => r.data.data),
  });

export const useCreateExpenseGroup = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: expenseGroupsApi.create,
    onSuccess: (res) => {
      const created = res.data.data;
      qc.setQueryData(
        queryKeys.expense_groups,
        (old: ExpenseGroup[] | undefined) =>
          old ? [...old, created] : [created],
      );
    },
  });
};

export const useUpdateExpenseGroup = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      groupId,
      data,
    }: {
      groupId: number;
      data: UpdateExpenseGroupPayload;
    }) => expenseGroupsApi.update(groupId, data),
    onSuccess: (res) => {
      const updated = res.data.data;

      // update the single group cache
      qc.setQueryData(queryKeys.expense_group(updated.id), updated);

      // update it inside the list too
      qc.setQueryData(
        queryKeys.expense_groups,
        (old: ExpenseGroup[] | undefined) =>
          old?.map((g) => (g.id === updated.id ? updated : g)),
      );
    },
  });
};

export const useDeleteExpenseGroup = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => expenseGroupsApi.delete(id),
    onSuccess: (_, id) => {
      qc.removeQueries({ queryKey: queryKeys.expense_group(id) });
      qc.setQueryData(queryKeys.expense_groups, (old: ExpenseGroup[]) =>
        old.filter((g) => g.id !== id),
      );
    },
  });
};

export const useInviteMembers = (groupId: number) => {
  return useMutation({
    mutationFn: (data: { members: { username: string }[] }) =>
      expenseGroupsApi.invite(groupId, data),
    // Inviting sends pending Notification rows, not
    // ExpenseGroupMember rows. Group membership only changes once the invitee accepts
  });
};

export const useUpdateGroupMember = (groupId: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      user_id,
      data,
    }: {
      user_id: number;
      data: { default_split_ratio?: number; role?: string };
    }) => expenseGroupsApi.updateMember(groupId, user_id, data),
    onSuccess: (res) => {
      const updated = res.data.data;
      qc.setQueryData(
        queryKeys.expense_group(groupId),
        (old: ExpenseGroup | undefined) => {
          if (!old) return old;
          return {
            ...old,
            members: old.members.map((m) =>
              m.user_id === updated.user_id ? { ...m, ...updated } : m,
            ),
          };
        },
      );
    },
  });
};

export const useBulkUpdateGroupMembers = (groupId: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (
      members: {
        user_id: number;
        default_split_ratio?: number;
        role?: string;
      }[],
    ) => expenseGroupsApi.bulkUpdateMembers(groupId, members),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.expense_group(groupId) });
    },
  });
};

export const useRemoveMembers = (groupId: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (member_ids: number[]) =>
      expenseGroupsApi.removeMembers(groupId, member_ids),
    onSuccess: (_, member_ids) => {
      qc.setQueryData(
        queryKeys.expense_group(groupId),
        (old: ExpenseGroup | undefined) =>
          old
            ? { ...old, members: removeMembers(old.members, member_ids) }
            : old,
      );

      qc.setQueryData(
        queryKeys.expense_groups,
        (old: ExpenseGroup[] | undefined) =>
          old?.map((g) =>
            g.id === groupId
              ? { ...g, members: removeMembers(g.members, member_ids) }
              : g,
          ),
      );
    },
  });
};

export const useLeaveExpenseGroup = () => {
  const qc = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  return useMutation({
    mutationFn: (groupId: number) => expenseGroupsApi.leave(groupId),
    onSuccess: (_, groupId) => {
      if (currentUser) {
        qc.setQueryData(
          queryKeys.expense_group(groupId),
          (old: ExpenseGroup | undefined) =>
            old
              ? {
                  ...old,
                  members: removeMembers(old.members, [currentUser.id]),
                }
              : old,
        );

        qc.setQueryData(
          queryKeys.expense_groups,
          (old: ExpenseGroup[] | undefined) =>
            old?.map((g) =>
              g.id === groupId
                ? { ...g, members: removeMembers(g.members, [currentUser.id]) }
                : g,
            ),
        );
      }
    },
  });
};

export const useSettlement = (id: number) =>
  useQuery({
    queryKey: queryKeys.settlement(id),
    queryFn: () => expenseGroupsApi.getSettlement(id).then((r) => r.data.data),
  });

//--------------------------------------------------------------------------------
// Expenses
//--------------------------------------------------------------------------------
export const useExpenses = (params?: { expense_group_id?: number }) =>
  useQuery({
    queryKey: queryKeys.expenses(params),
    queryFn: () => expensesApi.getAll(params).then((r) => r.data.data),
  });

export const useExpensesPaginated = (params: ExpenseListParams) =>
  useQuery({
    queryKey: queryKeys.expenses(params),
    queryFn: () => expensesApi.getPaginated(params).then((r) => r.data.data),
    placeholderData: keepPreviousData,
    staleTime: 15_000, // shorter than the app default - groupmates edit these too
  });

export const useExpensePayees = (expenseGroupId: number) =>
  useQuery({
    queryKey: queryKeys.expensePayees(expenseGroupId),
    queryFn: () =>
      expensesApi.getPayees(expenseGroupId).then((r) => r.data.data),
    staleTime: 15_000,
  });

export const useCreateExpense = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: expensesApi.create,
    onSuccess: (res) => {
      const created = res.data.data;
      const key = queryKeys.expenses(
        created.expense_group_id
          ? { expense_group_id: created.expense_group_id }
          : undefined,
      );

      qc.setQueryData(key, (old: Expense[] | undefined) =>
        old ? [...old, created] : [created],
      );
      qc.invalidateQueries({ queryKey: ["expenses"] });
      if (created.expense_group_id) {
        qc.invalidateQueries({
          queryKey: queryKeys.settlement(created.expense_group_id),
        });
      }
    },
  });
};

export const useUpdateExpense = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateExpensePayload }) =>
      expensesApi.update(id, data),
    onSuccess: (res) => {
      const updated = res.data.data;
      const key = queryKeys.expenses(
        updated.expense_group_id
          ? { expense_group_id: updated.expense_group_id }
          : undefined,
      );
      qc.setQueryData(key, (old: Expense[] | undefined) =>
        old?.map((ex) => (ex.id === updated.id ? updated : ex)),
      );
      qc.invalidateQueries({ queryKey: ["expenses"] });

      if (updated.expense_group_id) {
        qc.invalidateQueries({
          queryKey: queryKeys.settlement(updated.expense_group_id),
        });
      }
    },
  });
};

export const useDeleteExpense = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id }: { id: number; expense_group_id?: number }) =>
      expensesApi.delete(id),
    onSuccess: (_, { id, expense_group_id }) => {
      const key = queryKeys.expenses(
        expense_group_id ? { expense_group_id } : undefined,
      );
      qc.setQueryData(key, (old: Expense[] | undefined) =>
        old?.filter((ex) => ex.id !== id),
      );
      qc.invalidateQueries({ queryKey: ["expenses"] });
      if (expense_group_id) {
        qc.invalidateQueries({
          queryKey: queryKeys.settlement(expense_group_id),
        });
      }
    },
  });
};

//--------------------------------------------------------------------------------
// Notifications
//--------------------------------------------------------------------------------
export const useNotifications = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: () => notificationsApi.getAll().then((r) => r.data.data),
    enabled: isAuthenticated,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
  });
};

export const useMarkNotificationRead = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: (_, id) => {
      qc.setQueryData(
        queryKeys.notifications,
        (old: Notification[] | undefined) => old?.filter((n) => n.id !== id),
      );
    },
  });
};

export const useRespondToInvitation = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, accept }: { id: number; accept: boolean }) =>
      notificationsApi.respondInvitation(id, accept),
    onSuccess: (_, { id, accept }) => {
      const current = qc.getQueryData<Notification[]>(queryKeys.notifications);
      const responded = current?.find((n) => n.id === id);

      if (accept && responded?.expense_group_id != null) {
        qc.invalidateQueries({
          queryKey: queryKeys.expense_group(responded.expense_group_id),
        });
        qc.invalidateQueries({ queryKey: queryKeys.expense_groups });
      }

      qc.setQueryData(
        queryKeys.notifications,
        (old: Notification[] | undefined) => old?.filter((n) => n.id !== id),
      );
    },
  });
};
