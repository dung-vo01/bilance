# Expense sharing & settlement

How split ratios, expense shares, and settlement balances relate to each
other.

## Tables

**`ExpenseGroupMember`**
- `user_id`, `expense_group_id`
- `default_split_ratio` — the ratio applied to *new* expenses by default

**`ExpenseShare`** (one row per member, per expense)
- `expense_id`, `user_id`
- `ratio` — snapshotted at creation time, editable per expense
- `amount` — `value * ratio`, recalculated whenever the expense value changes

## Rules

- Creating an expense auto-generates `ExpenseShare` rows from each member's
  current `default_split_ratio`.
- Shares can be adjusted per expense: edit individual ratios, add a member
  who wasn't in the original split, but ratios must always sum to 1.0.
- Settlement is computed from `ExpenseShare` only — it never reads
  `default_split_ratio` directly.
- Changing a member's `default_split_ratio` only affects expenses created
  afterward; past shares are immutable unless explicitly edited.

**`Repayment`** (one row per recorded payment between two members)
- `expense_group_id`, `from_user_id` (payer), `to_user_id` (payee),
  `created_by_id`
- `amount`, `paid_at` (defaults to now), `note`
- `is_deleted`, `deleted_at`, `deleted_by_id`, `deleted_note` — set when the
  repayment is undone (see [Repayments](#repayments))

DB constraints: `amount > 0`, `from_user_id != to_user_id`, and
`is_deleted` must agree with `deleted_at IS NOT NULL`.

## Settlement

Settlement is computed on demand from expenses, shares and repayments —
nothing is stored. For each member:
- `paid` = sum of expense values where `payee_id` = that member
- `owes` = sum of `ExpenseShare.amount` where `user_id` = that member
- `sent` = sum of active (not undone) repayments where that member is
  `from_user_id`
- `received` = sum of active repayments where that member is `to_user_id`
- `balance` = `paid - owes + sent - received`

A positive balance means the group owes that member; a negative one means
they owe the group. Paying someone back moves your balance towards zero and
theirs towards zero too, so a fully repaid debt disappears from the result.

"Who pays who" (`transactions`) is derived from the balances with a greedy
match: debtors (largest debt first) are paired with creditors (largest credit
first) until everyone is at zero. It isn't tracked per-expense, so it's a
minimal set of payments rather than a record of which expense each one covers.

### Pending expenses

An expense with no `ExpenseShare` rows has no split yet. It is returned
separately as `pending_expenses` / `pending_total` and does **not** affect
balances until it gets a split. `total` is `settled_total + pending_total`.

### Imbalance

`imbalance` is the sum of all balances. It should be ~0; if it drifts past a
rounding tolerance (0.005 per share) the server logs a warning. It's returned
in the response but not yet surfaced in the UI.

## Repayments

A repayment records that `from_user` has paid `to_user`. In the UI it is
created by pressing **Resolve** on a "Who pays who" entry.

**Create** (`POST /expense-groups/{id}/repayments`)
1. Only an app admin, a group admin, or the payer/payee may create it.
2. The group row is locked (`SELECT ... FOR UPDATE`) so concurrent requests
   can't both resolve the same debt.
3. The settlement is recomputed and the request must match a current
   `from → to` transaction (amount within 0.01); otherwise the server returns
   `409 Settlement has changed, please refresh!`. The UI refetches on
   settle/error, so a stale screen corrects itself.

**Unresolve** (`POST /expense-groups/{id}/repayments/{id}/unresolve`)
- Same authorization as create (checked after locking the group).
- Soft-deletes the row: `is_deleted`, `deleted_at`, `deleted_by_id` and an
  optional `deleted_note` are set. An undone repayment stops counting towards
  `sent` / `received`, so the debt reappears in "Who pays who".
- A repayment can only be undone once (`409` the second time). Resolving the
  same debt again creates a **new** row, so history is never overwritten.

**History** (`GET /expense-groups/{id}/repayments`)
- Group members (and app admins) only. Newest `paid_at` first, including
  undone rows, so the full audit trail is visible.

Repayments are immutable ledger entries: there is no edit endpoint, only
create and unresolve. Deleting a group deletes its repayments.

## Guest sandbox data

`POST /auth/guest` seeds a "Sample Trip" group with the shared companion user
"Alex": two split expenses, one pending expense, one active repayment and one
undone repayment (€60 still shown under "Who pays who"). That way every
settlement feature is visible to a guest right away. Guest data is deleted
after `GUEST_ACCOUNT_TTL_HOURS` or on guest logout.

## Edge cases

- A member removed from the group keeps their shares and repayments on past
  entries — they're labeled "former member" rather than dropped from the data.
- Adding a share that would push the total ratio over 1.0 is rejected,
  both client- and server-side.
- All ratios set to 0 except one is valid — that person owes the full amount.
- Money is stored as floats and rounded to 2 decimals, which is why repayment
  matching allows 0.01 of tolerance and balances under 0.005 are treated as
  zero in the UI. Moving to integer cents would remove the need for both.
