# Bilance Backend

FastAPI + async SQLAlchemy 2.0 + PostgreSQL backend for Bilance.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your values
```

Email (verification, password reset, group-invitation and friend-request
notices) is sent via
[SendGrid](https://sendgrid.com), using their free **Single Sender
Verification** - verify one email address you control (they email you a
confirmation link, no domain or DNS setup needed), set `EMAIL_FROM` to that
address, and you can then send to any real recipient. Without
`SENDGRID_API_KEY` set, sends are skipped with a log line instead of
failing, so local dev works without an account.

A [Resend](https://resend.com)-based implementation
(`email_service._send_resend`) is also kept in the codebase but unused -
Resend only supports verifying a full domain (no single-address option), so
switching to it means owning a domain. To re-enable it, point the public
`send_*` functions at `_send_resend` instead of `_send` and set
`RESEND_API_KEY`.

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
| GET              | /api/users                                      | List/search users (admin only)                                                                                                                                                                                                                       |
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
| GET              | /api/notifications                              | My unread notifications (incl. pending invitations and friend requests)                                                                                                                                                                              |
| POST             | /api/notifications/{id}/read                    | Mark as read                                                                                                                                                                                                                                         |
| POST             | /api/notifications/invitations/{id}/respond     | Accept/decline a group invitation                                                                                                                                                                                                                    |
| POST             | /api/notifications/contacts/{id}/respond        | Accept/decline a friend request - on accept, creates the contact relationship both ways and notifies the requester (no email, in-app only)                                                                                                          |
| GET              | /api/contacts                                   | Invite-eligible people - accepted contacts plus anyone you already share a group with                                                                                                                                                               |
| GET              | /api/contacts/detail                            | Your real contacts only, with email/phone and any shared groups attached                                                                                                                                                                             |
| POST             | /api/contacts/requests                          | Send a friend request by exact username - creates a pending notification and emails the recipient                                                                                                                                                   |
| GET              | /api/contacts/requests/sent                     | Your outgoing pending friend requests                                                                                                                                                                                                                |
| DELETE           | /api/contacts/requests/{notification_id}        | Cancel a friend request you sent                                                                                                                                                                                                                     |
| DELETE           | /api/contacts/{user_id}                         | Unfriend - removes the contact relationship both ways (doesn't affect shared group membership)                                                                                                                                                      |
