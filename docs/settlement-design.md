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

## Settlement

For each member:
- `paid` = sum of expense values where `payee_id` = that member
- `owes` = sum of `ExpenseShare.amount` where `user_id` = that member
- `balance` = `paid - owes`

## Edge cases

- A member removed from the group keeps their shares on past expenses —
  they're labeled "former member" rather than dropped from the data.
- Adding a share that would push the total ratio over 1.0 is rejected,
  both client- and server-side.
- All ratios set to 0 except one is valid — that person owes the full amount.
