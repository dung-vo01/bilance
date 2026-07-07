# Bilance Backend

FastAPI + async SQLAlchemy 2.0 + PostgreSQL backend for Bilance.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # fill in your values
```

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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Liveness/readiness (checks DB) |
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login |
| POST | /api/auth/refresh | Refresh token (refresh JWT as Bearer header) |
| GET | /api/auth/me | Current user |
| GET | /api/users | List/search users |
| POST | /api/users | Create user (admin only) |
| GET/PATCH/DELETE | /api/users/{id} | Get/update/delete user |
| GET | /api/expense-groups | List my groups |
| POST | /api/expense-groups | Create group |
| GET/PATCH/DELETE | /api/expense-groups/{id} | Get/update/delete group |
| POST | /api/expense-groups/{id}/invite | Invite members (creates a pending notification, not an immediate membership) |
| POST | /api/expense-groups/{id}/leave | Leave group |
| PATCH | /api/expense-groups/{id}/members/{user_id} | Update one member |
| PATCH | /api/expense-groups/{id}/members | Bulk update members |
| DELETE | /api/expense-groups/{id}/members?member_ids=1,2 | Remove members |
| GET | /api/expense-groups/{id}/settlement | Who-owes-who settlement |
| GET | /api/expenses | List expenses (personal, or `?expense_group_id=`) |
| POST | /api/expenses | Create expense |
| PATCH/DELETE | /api/expenses/{id} | Update/soft-delete expense |
| GET | /api/categories | List categories (global + personal/group) |
| POST | /api/categories | Create category |
| PATCH/DELETE | /api/categories/{id} | Update/delete category |
| GET | /api/notifications | My unread notifications (incl. pending invitations) |
| POST | /api/notifications/{id}/read | Mark as read |
| POST | /api/notifications/invitations/{id}/respond | Accept/decline a group invitation |
