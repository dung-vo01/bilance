from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.expense_group import ExpenseGroup
    from app.models.user import User


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])

    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped["User | None"] = relationship(foreign_keys=[updated_by_id])

    expense_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("expense_groups.id")
    )
    expense_group: Mapped["ExpenseGroup | None"] = relationship(
        foreign_keys=[expense_group_id]
    )
