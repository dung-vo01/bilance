# Bilance Backend

FastAPI + async SQLAlchemy 2.0 + PostgreSQL backend for Bilance.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your values
```

Email (verification, password reset, group-invitation notices) is sent via plain **SMTP** through a real mailbox - set `SMTP_HOST`/`SMTP_PORT` for the provider, `SMTP_USERNAME`/`SMTP_PASSWORD` for the account (for Gmail, this means turning on 2-Step Verification and generating a 16-character [App Password](https://myaccount.google.com/apppasswords) - your normal
password won't work), and `EMAIL_FROM` to that same address. Without `SMTP_USERNAME`/`SMTP_PASSWORD` set, sends are skipped with a log line instead of failing, so local dev works without any of this configured.

Previous HTTP-API-based implementation is also kept in the codebase but unused, in case SMTP ever needs swapping out:

- `email_service._send_resend` - [Resend](https://resend.com), which only supports full-domain verification (no single-address option), so needs owning a domain to use.

## Database

```bash
alembic upgrade head
```

## Run

```bash
uvicorn main:app --reload
```

Or via Docker Compose (starts Postgres too):

```bash
docker compose up --build
```

## Tests

```bash
pytest
```

Requires a `TEST_DATABASE_URL` Postgres database (see `.env.example`); the
suite creates/drops its own schema and wraps each test in a rolled-back
transaction, so it's safe to point at any throwaway database.

## Project Structure

```
app/
├── core/                 # config, security (JWT + bcrypt), auth deps, exceptions, logging
├── db/                   # async engine/session setup
├── models/               # SQLAlchemy 2.0 declarative models
├── schemas/              # Pydantic request/response models
├── services/             # business logic (async functions, db session passed explicitly)
└── routers/              # FastAPI routers (one per resource)
migrations/                # standalone Alembic env + versions
tests/                      # pytest + httpx.AsyncClient suite
```

Interactive API docs are served at `/docs` (Swagger UI) and `/redoc` once the
app is running.

## API Overview

| Method           | Endpoint                                        | Description                                                                                                                                                                                                                                          |
| ---------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET              | /health                                         | Liveness/readiness (checks DB)                                                                                                                                                                                                                       |
| POST             | /api/auth/register                              | Register - creates an unverified account and emails a verification link; does not return tokens                                                                                                                                                      |
| POST             | /api/auth/verify-email/{token}                  | Verify email from the emailed link                                                                                                                                                                                                                   |
| POST             | /api/auth/resend-verification                   | Resend the verification email (enumeration-safe response)                                                                                                                                                                                            |
| POST             | /api/auth/forgot-password                       | Email a password-reset link (enumeration-safe response)                                                                                                                                                                                              |
| POST             | /api/auth/reset-password                        | Set a new password from a reset token                                                                                                                                                                                                                |
| POST             | /api/auth/guest                                 | Create and log into a pre-seeded guest sandbox account, no signup required                                                                                                                                                                           |
| POST             | /api/auth/guest/logout                          | Immediately delete the current guest's account and data (real users get a 403)                                                                                                                                                                       |
| POST             | /api/auth/login                                 | Login - blocked with 403 until the account's email is verified                                                                                                                                                                                       |
| POST             | /api/auth/refresh                               | Refresh token (refresh JWT as Bearer header)                                                                                                                                                                                                         |
| GET              | /api/auth/me                                    | Current user                                                                                                                                                                                                                                         |
| GET              | /api/users                                      | List/search users                                                                                                                                                                                                                                    |
| POST             | /api/users                                      | Create user (admin only)                                                                                                                                                                                                                             |
| GET/PATCH/DELETE | /api/users/{id}                                 | Get/update/delete user                                                                                                                                                                                                                               |
| GET              | /api/expense-groups                             | List my groups                                                                                                                                                                                                                                       |
| POST             | /api/expense-groups                             | Create group                                                                                                                                                                                                                                         |
| GET/PATCH/DELETE | /api/expense-groups/{id}                        | Get/update/delete group                                                                                                                                                                                                                              |
| POST             | /api/expense-groups/{id}/invite                 | Invite members (creates a pending notification and emails the invitee, not an immediate membership)                                                                                                                                                  |
| POST             | /api/expense-groups/{id}/leave                  | Leave group                                                                                                                                                                                                                                          |
| PATCH            | /api/expense-groups/{id}/members/{user_id}      | Update one member                                                                                                                                                                                                                                    |
| PATCH            | /api/expense-groups/{id}/members                | Bulk update members                                                                                                                                                                                                                                  |
| DELETE           | /api/expense-groups/{id}/members?member_ids=1,2 | Remove members                                                                                                                                                                                                                                       |
| GET              | /api/expense-groups/{id}/settlement             | Who-owes-who settlement                                                                                                                                                                                                                              |
| GET              | /api/expenses                                   | List expenses (personal, or `?expense_group_id=`). Supports `status`, `search_kw`, `category_id`/`no_category`, `payee_id`, `sort_by`, `sort_dir`; paginates (`{items, total, total_pages}`) when `page` is passed, otherwise returns the full array |
| GET              | /api/expenses/payees?expense_group_id=          | Distinct users who've paid an expense in a group, including former members                                                                                                                                                                           |
| POST             | /api/expenses                                   | Create expense                                                                                                                                                                                                                                       |
| PATCH/DELETE     | /api/expenses/{id}                              | Update/soft-delete expense                                                                                                                                                                                                                           |
| GET              | /api/categories                                 | List categories (global + personal/group)                                                                                                                                                                                                            |
| POST             | /api/categories                                 | Create category                                                                                                                                                                                                                                      |
| PATCH/DELETE     | /api/categories/{id}                            | Update/delete category                                                                                                                                                                                                                               |
| GET              | /api/notifications                              | My unread notifications (incl. pending invitations)                                                                                                                                                                                                  |
| POST             | /api/notifications/{id}/read                    | Mark as read                                                                                                                                                                                                                                         |
| POST             | /api/notifications/invitations/{id}/respond     | Accept/decline a group invitation                                                                                                                                                                                                                    |
