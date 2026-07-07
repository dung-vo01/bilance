from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz import is_app_admin, is_group_member
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Expense, ExpenseGroup, ExpenseGroupMember, ExpenseShare


async def calculate(db: AsyncSession, expense_group_id: int, user_id: int) -> dict:
    group_result = await db.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.id == expense_group_id)
        .options(selectinload(ExpenseGroup.members).selectinload(ExpenseGroupMember.user))
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise NotFoundError("Group not found")

    if not await is_app_admin(db, user_id) and not await is_group_member(
        db, expense_group_id, user_id
    ):
        raise ForbiddenError("Not a member of this group")

    expenses_result = await db.execute(
        select(Expense)
        .where(Expense.expense_group_id == expense_group_id, Expense.is_deleted.is_(False))
        .options(selectinload(Expense.shares).selectinload(ExpenseShare.user))
    )
    expenses = list(expenses_result.scalars().all())

    settled_expenses = [e for e in expenses if e.shares]
    settled_total = round(sum(e.value for e in settled_expenses), 2)

    pending_expenses = [
        {
            "id": e.id,
            "value": round(e.value, 2),
            "payee_id": e.payee_id,
            "name": e.name,
            "description": e.description,
        }
        for e in expenses
        if not e.shares
    ]
    pending_total = round(sum(e["value"] for e in pending_expenses), 2)

    # Calculate how much each member should pay based on split ratio
    member_data = {}
    for member in group.members:
        member_data[member.user_id] = {
            "user_id": member.user_id,
            "username": member.user.username if member.user else None,
            "paid": 0.0,
            "owes": 0.0,
        }

    # Calculate how much each member actually paid
    for expense in settled_expenses:
        # credit the payer
        if expense.payee_id in member_data:
            member_data[expense.payee_id]["paid"] += expense.value

        # debit each share
        for share in expense.shares:
            # former member — add them temporarily
            if share.user_id not in member_data:
                member_data[share.user_id] = {
                    "user_id": share.user_id,
                    "username": share.user.username if share.user else str(share.user_id),
                    "paid": 0.0,
                    "owes": 0.0,
                }
            member_data[share.user_id]["owes"] += share.amount

    members_list = []
    for uid, data in member_data.items():
        balance = round(data["paid"] - data["owes"], 2)
        members_list.append(
            {
                "user_id": uid,
                "username": data["username"],
                "paid": round(data["paid"], 2),
                "should_pay": round(data["owes"], 2),
                "balance": balance,
            }
        )

    # Calculate who owes who
    # Split members into creditors (balance > 0) and debtors (balance < 0)
    debtors = sorted(
        [dict(m) for m in members_list if m["balance"] < 0],
        key=lambda x: x["balance"],
    )
    creditors = sorted(
        [dict(m) for m in members_list if m["balance"] > 0],
        key=lambda x: x["balance"],
        reverse=True,
    )

    transactions = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]

        amount = round(min(-debtor["balance"], creditor["balance"]), 2)

        if amount > 0:
            transactions.append(
                {
                    "from_user_id": debtor["user_id"],
                    "to_user_id": creditor["user_id"],
                    "amount": amount,
                }
            )

        debtor["balance"] += amount
        creditor["balance"] -= amount

        if abs(debtor["balance"]) < 0.001:
            i += 1
        if abs(creditor["balance"]) < 0.001:
            j += 1

    return {
        "expense_group_id": expense_group_id,
        "members": members_list,
        "transactions": transactions,
        "pending_expenses": pending_expenses,
        "pending_total": pending_total,
        "settled_total": settled_total,
        "total": round(settled_total + pending_total, 2),
    }
