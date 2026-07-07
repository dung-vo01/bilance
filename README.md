# Bilance

## Tech

Frontend: React TypeScript, Tanstack (React query), Zustand
Backend: FastAPI, async SQLAlchemy 2.0 (asyncpg)
Database: PostgresQL
Host: Vercel

## V1

* Auth (register with username + email, login)
* Personal expense tracking
* Groups: create, invite by username, accept/decline, admin controls
* Group expenses with custom split ratios
* Categories (global + personal)
* Settlement view (who owes who)

## V2 

* Recurring payments
* Notification system, payment reminder/deadline
* Phone number registration
* Images support, AI integrated to extract data from images (maybe in V3 xd)


## Update mechanism on expense in group and settlement (V1 22nd June)

ExpenseGroupMember (existing table)
* user_id
* expense_group_id
* default_split_ratio  (renamed from split_ratio, this will be the default split ratio)


ExpenseShare (new table, unique for each member/expense)
* expense_id
* user_id
* ratio   (snapshotted ratio, editable per expense)
* amount  (value * ratio, recalculated on save)

Rules:
* When expense is created → auto-generate ExpenseShare rows from current member default_split_ratio
* User can edit shares on any expense — adjust existing individual ratios, add any current group member who wasn't in the original share, ratios must always sum to 1.0
* Settlement reads from ExpenseShare exclusively
* Changing default_split_ratio on a member → only affects future expenses
* Past expense shares are immutable unless explicitly edited

UI flow:
* Create expense → shares auto-calculated, shown as preview → user can adjust before saving
* Edit expense → can edit shares tab alongside name/amount/category
* Each expense detail shows "Shared between: John 60%, Bob 40%"

Settlement - for each user:
* paid = sum of expenses where payee_id = user_id
* owes = sum of ExpenseShare.amount where user_id = user_id
* balance = paid - owes

Edge cases:
* Member was removed from group but has shares on old expenses → keep their share, show as "former member"
* Member is added to the share but ratio would exceed 1.0 → validate and show error (frontend & backend) 
* All ratios set to 0 except one → valid, that person owes everything