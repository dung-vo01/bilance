from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_id
from app.db.session import get_db
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
from app.schemas.settlement import SettlementOut
from app.services import expense_group_service, settlement_service

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
async def invite_member(
    expense_group_id: int,
    data: InviteRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    notifications = await expense_group_service.invite(
        db, expense_group_id, user_id, data.members
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
