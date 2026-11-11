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

Or via Docker Compose (starts Postgres and Redis too):

```bash
docker compose up --build
```

You can also run just the infrastructure in Docker and the API on your
machine (hot reload, no rebuilds). Naming a service starts only that service:

```bash
docker compose up -d redis       # Redis only (optional, see "Rate limiting")
docker compose up -d db redis    # Postgres + Redis
docker compose ps                # status
docker compose stop redis        # stop one service
docker compose down              # stop and remove everything
```

If you already run Postgres natively, start only `redis` - the compose `db`
service would clash with your Postgres on port 5432.

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

| Method           | Endpoint                                                     | Description                                                                                                                                                                                                                                          |
| ---------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET              | /health                                                      | Liveness/readiness (checks DB)                                                                                                                                                                                                                       |
| POST             | /api/auth/register                                           | Register - creates an unverified account and emails a verification link; does not return tokens                                                                                                                                                      |
| POST             | /api/auth/verify-email/{token}                               | Verify email from the emailed link                                                                                                                                                                                                                   |
| POST             | /api/auth/resend-verification                                | Resend the verification email (enumeration-safe response)                                                                                                                                                                                            |
| POST             | /api/auth/forgot-password                                    | Email a password-reset link (enumeration-safe response)                                                                                                                                                                                              |
| POST             | /api/auth/reset-password                                     | Set a new password from a reset token                                                                                                                                                                                                                |
| POST             | /api/auth/guest                                              | Create and log into a pre-seeded guest sandbox account, no signup required (sample group with a pending expense and active + undone repayments)                                                                                                      |
| POST             | /api/auth/guest/logout                                       | Immediately delete the current guest's account and data (real users get a 403)                                                                                                                                                                       |
| POST             | /api/auth/login                                              | Login - blocked with 403 until the account's email is verified                                                                                                                                                                                       |
| POST             | /api/auth/refresh                                            | Refresh token (refresh JWT as Bearer header)                                                                                                                                                                                                         |
| GET              | /api/auth/me                                                 | Current user                                                                                                                                                                                                                                         |
| GET              | /api/users                                                   | List/search users (admin only)                                                                                                                                                                                                                       |
| POST             | /api/users                                                   | Create user (admin only)                                                                                                                                                                                                                             |
| GET/PATCH/DELETE | /api/users/{id}                                              | Get/update/delete user                                                                                                                                                                                                                               |
| GET              | /api/expense-groups                                          | List my groups                                                                                                                                                                                                                                       |
| POST             | /api/expense-groups                                          | Create group                                                                                                                                                                                                                                         |
| GET/PATCH/DELETE | /api/expense-groups/{id}                                     | Get/update/delete group                                                                                                                                                                                                                              |
| POST             | /api/expense-groups/{id}/invite                              | Invite members (creates a pending notification and emails the invitee, not an immediate membership)                                                                                                                                                  |
| POST             | /api/expense-groups/{id}/leave                               | Leave group                                                                                                                                                                                                                                          |
| PATCH            | /api/expense-groups/{id}/members/{user_id}                   | Update one member                                                                                                                                                                                                                                    |
| PATCH            | /api/expense-groups/{id}/members                             | Bulk update members                                                                                                                                                                                                                                  |
| DELETE           | /api/expense-groups/{id}/members?member_ids=1,2              | Remove members                                                                                                                                                                                                                                       |
| GET              | /api/expense-groups/{id}/settlement                          | Settlement - member balances (`paid - owes + sent - received`), who-pays-who `transactions`, and `pending_expenses` that have no split yet                                                                                                           |
| POST             | /api/expense-groups/{id}/repayments                          | Record that one member paid another (Resolve a who-pays-who entry). Must match a current settlement transaction, else 409; payer, payee, or an admin only. Returns 201                                                                               |
| GET              | /api/expense-groups/{id}/repayments                          | Repayment history, newest first, including undone ones (`is_deleted`)                                                                                                                                                                                |
| POST             | /api/expense-groups/{id}/repayments/{repayment_id}/unresolve | Undo a repayment (soft-delete, optional `deleted_note`); can only be undone once, re-resolving creates a new row                                                                                                                                     |
| GET              | /api/expenses                                                | List expenses (personal, or `?expense_group_id=`). Supports `status`, `search_kw`, `category_id`/`no_category`, `payee_id`, `sort_by`, `sort_dir`; paginates (`{items, total, total_pages}`) when `page` is passed, otherwise returns the full array |
| GET              | /api/expenses/payees?expense_group_id=                       | Distinct users who've paid an expense in a group, including former members                                                                                                                                                                           |
| POST             | /api/expenses                                                | Create expense                                                                                                                                                                                                                                       |
| PATCH/DELETE     | /api/expenses/{id}                                           | Update/soft-delete expense                                                                                                                                                                                                                           |
| GET              | /api/categories                                              | List categories (global + personal/group)                                                                                                                                                                                                            |
| POST             | /api/categories                                              | Create category                                                                                                                                                                                                                                      |
| PATCH/DELETE     | /api/categories/{id}                                         | Update/delete category                                                                                                                                                                                                                               |
| GET              | /api/notifications                                           | My unread notifications (incl. pending invitations and friend requests)                                                                                                                                                                              |
| POST             | /api/notifications/{id}/read                                 | Mark as read                                                                                                                                                                                                                                         |
| POST             | /api/notifications/invitations/{id}/respond                  | Accept/decline a group invitation                                                                                                                                                                                                                    |
| POST             | /api/notifications/contacts/{id}/respond                     | Accept/decline a friend request - on accept, creates the contact relationship both ways and notifies the requester (no email, in-app only)                                                                                                           |
| GET              | /api/contacts                                                | Invite-eligible people - accepted contacts plus anyone you already share a group with                                                                                                                                                                |
| GET              | /api/contacts/detail                                         | Your real contacts only, with email/phone and any shared groups attached                                                                                                                                                                             |
| POST             | /api/contacts/requests                                       | Send a friend request by exact username - creates a pending notification and emails the recipient                                                                                                                                                    |
| GET              | /api/contacts/requests/sent                                  | Your outgoing pending friend requests                                                                                                                                                                                                                |
| DELETE           | /api/contacts/requests/{notification_id}                     | Cancel a friend request you sent                                                                                                                                                                                                                     |
| DELETE           | /api/contacts/{user_id}                                      | Unfriend - removes the contact relationship both ways (doesn't affect shared group membership)                                                                                                                                                       |

## Rate limiting

Requests are rate limited per client IP with
[slowapi](https://github.com/laurentS/slowapi). Every route gets a default of
120 requests per minute (via `SlowAPIMiddleware`), and the abuse-prone routes
have stricter limits of their own, which replace the default for that route:

| Route                                    | Limit     | Why                                       |
| ---------------------------------------- | --------- | ----------------------------------------- |
| POST /api/auth/login                     | 10/minute | Password guessing (each try costs bcrypt) |
| POST /api/auth/guest                     | 10/hour   | Each call creates a user and seeds data   |
| POST /api/auth/register                  | 5/hour    | Sends a verification email                |
| POST /api/auth/resend-verification       | 5/hour    | Sends an email                            |
| POST /api/auth/forgot-password           | 5/hour    | Sends an email                            |
| POST /api/auth/reset-password            | 5/hour    | Token guessing                            |
| POST /api/contacts/requests              | 20/hour   | Sends an email                            |
| POST /api/expense-groups/{id}/invite     | 20/hour   | Sends an email                            |
| GET /health                              | exempt    | Used by the host's health checks          |

Each route has its own counter. When a limit is hit the API returns `429` with
the usual `{"success": false, "error": ...}` body and a `Retry-After` header
(seconds).

- **Storage** is set with `RATE_LIMIT_STORAGE_URI`. The default, `memory://`,
  keeps counters inside the process, which is only exact for a single worker
  (each uvicorn worker counts separately, and counters reset on restart). With
  more than one instance or worker, point it at Redis so they share counts and
  keep them across restarts. The `redis` package is already in
  `requirements.txt`.
- **Production** (Render) runs the `Dockerfile` with 2 uvicorn workers
  (`WEB_CONCURRENCY`), so it uses a Render Key Value (Redis) instance in the same
  region: set `RATE_LIMIT_STORAGE_URI` on the web service to the instance's
  internal URL. It is the free plan with no persistence, which is fine for
  counters that expire on their own.
- **Local Redis** runs from the compose file (`docker compose up -d redis`);
  set `RATE_LIMIT_STORAGE_URI=redis://localhost:6379` in your `.env`. The port
  is published on `127.0.0.1` only, because Redis has no password here. Inside
  Compose the app uses `redis://redis:6379`. Counters are stored as
  `LIMITS:LIMITER/<ip>/<path>/<amount>/<multiple>/<unit>` keys with a TTL equal
  to the window, so Redis cleans them up on its own.
- **If Redis is down** the limiter fails open: after a 1-second connect/read
  timeout it logs a warning, falls back to in-memory counters (so limits become
  per-process) and switches back when Redis returns. Requests are never
  rejected because of a limiter outage.
- **Behind a proxy** (Render, etc.) the client IP comes from `X-Forwarded-For`.
  The `Dockerfile` start command passes `--forwarded-allow-ips '*'` to uvicorn
  (Render runs the Dockerfile and ignores the `Procfile`); without it every user
  would appear to come from the proxy's IP and share one counter. Only use `"*"`
  when the app is reachable only through the host's proxy.
- **Middleware order** in `main.py` matters: CORS must be the outermost layer so
  that 429 responses still carry CORS headers and browsers show the message
  instead of a CORS error.
- **Tests** always use `memory://` (set at the top of `tests/conftest.py`, so a
  Redis URL in your `.env` is ignored) and turn the limiter off globally with an
  autouse fixture; `tests/test_rate_limit.py` re-enables it per test.
