from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.core.deps import get_current_user_id
from app.db.session import get_db
from app.models.notification import NotificationType
from app.schemas.common import envelope
from app.schemas.expense_group import (
    BulkMemberUpdateRequest,
    ExpenseGroupCreate,
    ExpenseGroupOut,
    ExpenseGroupUpdate,
    InviteRequest,
    MemberOut,
    MemberUpdate,
)
from app.schemas.notification import NotificationOut
from app.schemas.repayment import RepaymentCreate, RepaymentOut, RepaymentUnresolve
from app.schemas.settlement import SettlementOut
from app.services import (
    email_service,
    expense_group_service,
    repayment_service,
    settlement_service,
)

router = APIRouter()


@router.get("")
async def list_groups(
    user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)
):
    groups = await expense_group_service.get_user_expense_groups(db, user_id)
    return envelope(
        [ExpenseGroupOut.model_validate(g).model_dump(mode="json") for g in groups]
    )


@router.post("", status_code=201)
async def create_group(
    data: ExpenseGroupCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    group = await expense_group_service.create(db, user_id, data)
    return envelope(ExpenseGroupOut.model_validate(group).model_dump(mode="json"))


@router.get("/{expense_group_id}")
async def get_group(
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    group = await expense_group_service.get(db, expense_group_id, user_id)
    return envelope(ExpenseGroupOut.model_validate(group).model_dump(mode="json"))


@router.patch("/{expense_group_id}")
async def update_group(
    expense_group_id: int,
    data: ExpenseGroupUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    group = await expense_group_service.update(db, expense_group_id, user_id, data)
    return envelope(ExpenseGroupOut.model_validate(group).model_dump(mode="json"))


@router.delete("/{expense_group_id}")
async def delete_group(
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await expense_group_service.delete(db, expense_group_id, user_id)
    return envelope({"message": "Group deleted"})


@router.post("/{expense_group_id}/invite")
@limiter.limit("20/hour")
async def invite_member(
    request: Request,
    expense_group_id: int,
    data: InviteRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    notifications = await expense_group_service.invite(
        db, expense_group_id, user_id, data.members
    )
    for n in notifications:
        if n.type == NotificationType.GROUP_INVITATION and n.recipient.email:
            background_tasks.add_task(
                email_service.send_group_invitation_email,
                n.recipient.email,
                n.recipient.firstname,
                n.recipient.username,
                n.actor.firstname or n.actor.username if n.actor else "Someone",
                n.expense_group_name,
            )
    return envelope(
        [
            NotificationOut.model_validate(n).model_dump(mode="json")
            for n in notifications
        ]
    )


@router.post("/{expense_group_id}/leave")
async def leave_group(
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await expense_group_service.leave(db, expense_group_id, user_id)
    return envelope({"message": "Left group"})


@router.patch("/{expense_group_id}/members/{member_user_id}")
async def update_group_member(
    expense_group_id: int,
    member_user_id: int,
    data: MemberUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    member = await expense_group_service.update_member(
        db, expense_group_id, current_user_id, member_user_id, data
    )
    return envelope(MemberOut.model_validate(member).model_dump(mode="json"))


@router.patch("/{expense_group_id}/members")
async def bulk_update_members(
    expense_group_id: int,
    data: BulkMemberUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    results = await expense_group_service.bulk_update_members(
        db, expense_group_id, current_user_id, data.members
    )
    return envelope(
        [MemberOut.model_validate(m).model_dump(mode="json") for m in results]
    )


@router.delete("/{expense_group_id}/members")
async def remove_member(
    expense_group_id: int,
    member_ids: str = Query(""),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ids = [int(i) for i in member_ids.split(",") if i]
    await expense_group_service.remove_members(db, expense_group_id, user_id, ids)
    return envelope({"message": "Member removed"})


@router.get("/{expense_group_id}/settlement")
async def get_settlement(
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await settlement_service.calculate(db, expense_group_id, user_id)
    return envelope(SettlementOut.model_validate(result).model_dump(mode="json"))


@router.post("/{expense_group_id}/repayments", status_code=201)
async def create_repayment(
    data: RepaymentCreate,
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await repayment_service.create(db, expense_group_id, user_id, data)
    return envelope(RepaymentOut.model_validate(result).model_dump(mode="json"))


@router.get("/{expense_group_id}/repayments")
async def get_repayments(
    expense_group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repayments = await repayment_service.get_all(db, expense_group_id, user_id)
    return envelope(
        [RepaymentOut.model_validate(rp).model_dump(mode="json") for rp in repayments]
    )


@router.post("/{expense_group_id}/repayments/{repayment_id}/unresolve")
async def unresolve_repayment(
    expense_group_id: int,
    repayment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    data: RepaymentUnresolve | None = None,
):
    result = await repayment_service.unresolve(
        db, expense_group_id, repayment_id, user_id, data or RepaymentUnresolve()
    )
    return envelope(RepaymentOut.model_validate(result).model_dump(mode="json"))
