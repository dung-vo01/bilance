from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.expense_group import ExpenseGroup
    from app.models.user import User


class Repayment(Base, TimestampMixin):
    __tablename__ = "repayments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_repayments_positive_amount"),
        CheckConstraint(
            "from_user_id != to_user_id", name="ck_repayments_different_users"
        ),
        CheckConstraint(
            "is_deleted = (deleted_at IS NOT NULL)",
            name="ck_repayments_deleted_consistent",
        ),
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    note: Mapped[str | None] = mapped_column(String)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_note: Mapped[str | None] = mapped_column(String)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_id])

    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    from_user: Mapped["User"] = relationship(foreign_keys=[from_user_id])

    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    to_user: Mapped["User"] = relationship(foreign_keys=[to_user_id])

    deleted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    deleted_by: Mapped["User | None"] = relationship(foreign_keys=[deleted_by_id])

    expense_group_id: Mapped[int] = mapped_column(
        ForeignKey("expense_groups.id"), index=True
    )
    expense_group: Mapped["ExpenseGroup"] = relationship(
        foreign_keys=[expense_group_id], back_populates="repayments"
    )
