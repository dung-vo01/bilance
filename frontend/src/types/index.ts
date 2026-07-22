export interface User {
  id: number;
  username: string;
  email: string;
  firstname: string | null;
  lastname: string | null;
  phone_number: string | null;
  role: "admin" | "member";
  is_active: boolean;
  is_email_verified: boolean;
  is_guest: boolean;
  created_at: string;
}

export interface ExpenseGroup {
  id: number;
  name: string;
  description: string | null;
  created_by_id: number;
  members: ExpenseGroupMember[];
  pending_invitations: NotificationActor[];
}

export interface ExpenseGroupMember {
  user_id: number;
  expense_group_id: number;
  role: "admin" | "member";
  default_split_ratio: number;
  user?: User;
}

export interface Expense {
  id: number;
  name: string;
  description: string | null;
  value: number;
  is_deleted: boolean;
  category_id: number | null;
  payee_id: number;
  expense_group_id: number | null;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  category?: Category;
  payee?: User;
  paid_at: string | null;
  shares: ExpenseShare[];
}

export interface Category {
  id: number;
  name: string;
  description: string;
  is_global: boolean;
  created_by_id: number | null;
  expense_group_id: number | null;
}

export interface PendingExpense {
  id: number;
  value: number;
  payee_id: number;
  name: string;
  description: string | null;
}
export interface Settlement {
  expense_group_id: number;
  members: SettlementMember[];
  transactions: Transaction[];
  pending_expenses: PendingExpense[];
  pending_total: number;
  settled_total: number;
  total: number;
}

export interface SettlementMember {
  user_id: number;
  username: string;
  should_pay: number;
  paid: number;
  balance: number;
}

export interface Transaction {
  from_user_id: number;
  to_user_id: number;
  amount: number;
}

export type NotificationType =
  | "group_invitation"
  | "invitation_accepted"
  | "invitation_declined"
  | "member_removed"
  | "member_left"
  | "members_invited"
  | "contact_request"
  | "contact_accepted"
  | "contact_declined";

// Mirrors backend UserPublicOut (no email)
export interface NotificationActor {
  id: number;
  username: string;
  firstname: string | null;
  lastname: string | null;
  role: "admin" | "member";
  is_active: boolean;
  phone_number: string | null;
  created_at: string;
}

// Shape returned by GET /api/contacts - same as UserPublicOut, no email
export type ContactUser = NotificationActor;

// A lighter reference to a person embedded in a notification's payload
// (e.g. someone who was removed or invited) — just enough to display a name.
export interface NotificationPersonRef {
  username: string;
  firstname?: string | null;
  lastname?: string | null;
}

export interface NotificationPayload {
  default_split_ratio?: number;
  removed_user_id?: number;
  removed_user?: NotificationPersonRef | null;
  invited_users?: NotificationPersonRef[];
  [key: string]: unknown;
}

export interface Notification {
  id: number;
  type: NotificationType;
  recipient_id: number;
  actor_id: number | null;
  actor: NotificationActor | null;
  expense_group_id: number | null;
  payload: NotificationPayload | null;
  is_read: boolean;
  read_at: string | null;
  resolved_at: string | null;
  created_at: string;
  expense_group_name: string | null;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
}

export interface ApiError {
  success: false;
  error: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}

export type NewUserPayload = {
  username: string;
  email: string;
  firstname: string | null;
  lastname: string | null;
  phone_number: string | null;
  role: "admin" | "member";
};

export type UpdateUserPayload = {
  firstname?: string;
  lastname?: string;
  phone_number?: string | null;
  role?: "admin" | "member";
  is_active?: boolean;
};

export type NewCategoryPayload = {
  name: string;
  description: string;
  expense_group_id?: number | null;
};

export type UpdateCategoryPayload = {
  name?: string;
  description?: string;
};

export type NewExpenseGroupPayload = {
  name: string;
  description?: string | null;
  members?: { id: number }[];
  split_ratios?: { user_id: number; default_split_ratio: number }[];
};

export type UpdateExpenseGroupPayload = {
  name?: string;
  description?: string;
};

export type NewExpensePayload = {
  name: string;
  description: string | null;
  value: number;
  category_id: number | null;
  payee_id: number | null;
  expense_group_id: number | null;
  paid_at: string | null;
  shares?: MemberExpenseShare[];
};

export type UpdateExpensePayload = {
  name?: string;
  description?: string | null;
  value?: number;
  category_id?: number | null;
  payee_id?: number;
  is_deleted?: boolean;
  paid_at?: string | null;
  shares?: MemberExpenseShare[];
};

export type InviteMember = {
  username: string;
  default_split_ratio: number;
};

export interface ExpenseShare {
  id: number;
  expense_id: number;
  user_id: number;
  ratio: number;
  amount: number;
  user?: User;
}

export type MemberExpenseShare = {
  user_id: number;
  ratio: number;
};

export type ExpenseStatusFilter = "all" | "active" | "deleted";
export type ExpenseSortBy = "name" | "paid_at" | "created_at" | "value";
export type SortDir = "asc" | "desc";

export type ExpenseListParams = {
  expense_group_id?: number;
  status?: ExpenseStatusFilter;
  search_kw?: string;
  category_id?: number;
  no_category?: boolean;
  payee_id?: number;
  sort_by?: ExpenseSortBy;
  sort_dir?: SortDir;
  page?: number;
  page_size?: number;
};

export interface PaginatedExpenses {
  items: Expense[];
  total: number;
  total_value: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CategoryBreakdownItem {
  category_id: number | null;
  category_name: string;
  total: number;
  percentage: number;
}

export interface CategoryBreakdown {
  period_days: number;
  total: number;
  categories: CategoryBreakdownItem[];
}
