import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
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

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="payee", foreign_keys="Expense.payee_id"
    )
