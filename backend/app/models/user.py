import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.expense import Expense


class AppRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    firstname: Mapped[str | None] = mapped_column(String)
    lastname: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    phone_number: Mapped[str | None] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[AppRole] = mapped_column(
        Enum(AppRole, name="approle"), default=AppRole.MEMBER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_verification_token_hash: Mapped[str | None] = mapped_column(String)
    email_verification_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    password_reset_token_hash: Mapped[str | None] = mapped_column(String)
    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="payee", foreign_keys="Expense.payee_id"
    )
