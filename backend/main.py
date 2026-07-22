from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, configure_logging

configure_logging(settings.LOG_LEVEL)

app = FastAPI(title="Bilance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

from app.routers import (
    auth,
    categories,
    contacts,
    expense_groups,
    expenses,
    health,
    notifications,
    users,
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api/users")
app.include_router(contacts.router, prefix="/api/contacts")
app.include_router(expense_groups.router, prefix="/api/expense-groups")
app.include_router(expenses.router, prefix="/api/expenses")
app.include_router(categories.router, prefix="/api/categories")
app.include_router(notifications.router, prefix="/api/notifications")
