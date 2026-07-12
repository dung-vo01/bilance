# Bilance

[![CI](https://github.com/dung-vo01/bilance/actions/workflows/ci.yml/badge.svg)](https://github.com/dung-vo01/bilance/actions/workflows/ci.yml)

A full-stack expense tracker for splitting shared costs with friends,
roommates, or any group - personal expenses and group expenses with
custom split ratios, invites, and a settlement view showing who owes who.

**[Live demo →](https://bilance.vercel.app/)**

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)
![Expense split](docs/screenshots/settlement.png)

## Features

- Auth with JWT access/refresh tokens
- Personal expense tracking - search, sort, filter by category/status,
  paginated
- Expense groups - create, invite by username, accept/decline, admin
  controls
- Per-expense split ratios, independent of a group's default ratio
- Settlement view - who owes who, and by how much
- Global and per-group expense categories
- Notifications for invitations and membership changes

## Tech stack

- **Frontend** - React, TypeScript, Vite, TanStack Query, Zustand, SCSS modules
- **Backend** - FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic
- **Auth** - JWT (access + refresh), bcrypt password hashing

## Project structure

```
backend/    FastAPI app  - see backend/README.md
frontend/   React app    - see frontend/README.md
docs/       design notes (expense sharing & settlement rules)
```

## Getting started

Follow the setup steps in [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md) to run the API and the app
locally.

> **Note:** if the backend is running on a free-tier host, it spins down
> when idle - the first request after a while can take up to a minute to
> wake it back up. The app shows a "waking up the server" message during
> that wait so it doesn't look stuck; subsequent requests are fast.

## Roadmap

- Recurring payments
- Payment due-date reminders
- Phone number registration
- Receipt image upload with AI-assisted data extraction
- Email sign-up and email notifications (invitations, reminders)

## License

&copy; 2026 Dung Vo. All rights reserved.
