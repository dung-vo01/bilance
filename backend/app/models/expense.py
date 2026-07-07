from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.expense_group import ExpenseGroup
    from app.models.user import User


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    value: Mapped[float | None] = mapped_column(Float)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category | None"] = relationship()

    payee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    payee: Mapped["User | None"] = relationship(
        back_populates="expenses", foreign_keys=[payee_id]
    )

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])

    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])

    expense_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("expense_groups.id")
    )
    expense_group: Mapped["ExpenseGroup | None"] = relationship()

    shares: Mapped[list["ExpenseShare"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan"
    )


class ExpenseShare(Base, TimestampMixin):
    __tablename__ = "expense_shares"
    __table_args__ = (
        UniqueConstraint("expense_id", "user_id", name="uq_expense_user_share"),
    )

    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ratio: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship()
    expense: Mapped["Expense"] = relationship(back_populates="shares")
