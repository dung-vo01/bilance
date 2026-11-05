from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import is_app_admin, is_group_admin, is_group_member
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.expense_group import ExpenseGroup, ExpenseGroupMember
from app.models.mixins import utcnow
from app.models.repayment import Repayment
from app.schemas.repayment import RepaymentCreate, RepaymentUnresolve
from app.services.settlement_service import compute_settlement, load_settlement_inputs


async def create(
    db: AsyncSession, expense_group_id: int, user_id: int, data: RepaymentCreate
) -> Repayment:
    # Only admins or current user is either from_user or to_user
    if (
        not await is_app_admin(db, user_id)
        and not await is_group_admin(db, expense_group_id, user_id)
        and not (user_id == data.from_user_id or user_id == data.to_user_id)
    ):
        raise ForbiddenError("You are not allowed to create repayment")

    # Lock the current expense group to make sure no one would change the amount during the process
    # Lock after authorization checks since payload provides enough input
    group_result = await db.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.id == expense_group_id)
        .options(
            selectinload(ExpenseGroup.members).selectinload(ExpenseGroupMember.user)
        )
        .with_for_update()
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise NotFoundError(f"Expense group (id={expense_group_id}) not found")

    expenses, repayments = await load_settlement_inputs(db, expense_group_id)

    current_settlement = compute_settlement(group, expenses, repayments)

    related_transaction = None
    for transaction in current_settlement["transactions"]:
        if (
            transaction["from_user_id"] == data.from_user_id
            and transaction["to_user_id"] == data.to_user_id
        ):
            related_transaction = transaction
            break

    # Send warning if the related transaction can not be found or the amount does not match
    if (
        related_transaction is None
        or abs(related_transaction["amount"] - data.amount) > 0.01
    ):
        raise ConflictError("Settlement has changed, please refresh!")

    repayment = Repayment(
        amount=data.amount,
        note=data.note,
        created_by_id=user_id,
        from_user_id=data.from_user_id,
        to_user_id=data.to_user_id,
        expense_group_id=expense_group_id,
    )

    if data.paid_at:
        repayment.paid_at = data.paid_at

    db.add(repayment)

    await db.commit()
    await db.refresh(
        repayment,
        attribute_names=["from_user", "to_user", "created_by", "deleted_by"],
    )

    return repayment


async def get_all(
    db: AsyncSession, expense_group_id: int, user_id: int
) -> list[Repayment]:
    if not await is_app_admin(db, user_id) and not await is_group_member(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Not a member of this group")

    group_result = await db.execute(
        select(ExpenseGroup).where(ExpenseGroup.id == expense_group_id)
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise NotFoundError(f"Expense group (id={expense_group_id}) not found")

    repayments_result = await db.execute(
        select(Repayment)
        .where(Repayment.expense_group_id == expense_group_id)
        .options(
            selectinload(Repayment.created_by),
            selectinload(Repayment.from_user),
            selectinload(Repayment.to_user),
            selectinload(Repayment.deleted_by),
        )
        .order_by(Repayment.paid_at.desc(), Repayment.id.desc())
    )

    return list(repayments_result.scalars().all())


async def unresolve(
    db: AsyncSession,
    expense_group_id: int,
    repayment_id: int,
    user_id: int,
    data: RepaymentUnresolve,
) -> Repayment:
    # Lock the current expense group to make sure no one would change the amount during the process
    # Lock first (different from create) since the authorization check needs input from group
    group_result = await db.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.id == expense_group_id)
        .with_for_update()
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise NotFoundError(f"Expense group (id={expense_group_id}) not found")

    repayment_result = await db.execute(
        select(Repayment).where(
            Repayment.id == repayment_id, Repayment.expense_group_id == expense_group_id
        )
    )

    repayment = repayment_result.scalar_one_or_none()
    if not repayment:
        raise NotFoundError(
            f"Repayment (id={repayment_id}) not found in expense group (id={expense_group_id})"
        )

    # Only admins or current user is either from_user or to_user
    if (
        not await is_app_admin(db, user_id)
        and not await is_group_admin(db, expense_group_id, user_id)
        and user_id not in (repayment.from_user_id, repayment.to_user_id)
    ):
        raise ForbiddenError(
            f"You are not allowed to unresolve this repayment (id={repayment_id})"
        )

    # Check if repayment is already unresolved: if so, raise an error
    # An repayment can only be unresolved once
    if repayment.is_deleted:
        raise ConflictError("Repayment was already unresolved")

    repayment.is_deleted = True
    repayment.deleted_at = utcnow()
    repayment.deleted_by_id = user_id
    repayment.deleted_note = data.deleted_note or None

    await db.commit()

    await db.refresh(
        repayment,
        attribute_names=["from_user", "to_user", "created_by", "deleted_by"],
    )

    return repayment
