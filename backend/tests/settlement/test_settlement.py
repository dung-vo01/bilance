import pytest

from app.models.mixins import utcnow


@pytest.mark.asyncio
async def test_settlement_balances_paid_minus_owed(
    auth_headers,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Dinner",
            "value": 100,
            "shares": [
                {"user_id": user.id, "ratio": 0.6},
                {"user_id": bob.id, "ratio": 0.4},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    _, balances = await get_settlement(headers, group_id)

    assert balances[user.id]["balance"] == pytest.approx(40.0)
    assert balances[bob.id]["balance"] == pytest.approx(-40.0)


@pytest.mark.asyncio
async def test_settlement_debt_simplification_transactions(
    auth_headers,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    carol = await create_user(username="carol", email="carol@example.com")

    members = [{"id": bob.id, "role": "member"}, {"id": carol.id, "role": "member"}]
    expenses = [
        {
            "name": "Hotel",
            "value": 90,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 3},
                {"user_id": bob.id, "ratio": 1 / 3},
                {"user_id": carol.id, "ratio": 1 / 3},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    data, _ = await get_settlement(headers, group_id)

    total_transacted = sum(t["amount"] for t in data["transactions"])
    assert total_transacted == pytest.approx(60.0)
    for txn in data["transactions"]:
        assert txn["to_user_id"] == user.id


@pytest.mark.asyncio
async def test_settlement_former_member_shares_still_counted(
    client,
    auth_headers,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Dinner",
            "value": 100,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    remove_resp = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={bob.id}", headers=headers
    )
    assert remove_resp.status_code == 200

    _, balances = await get_settlement(headers, group_id)

    assert bob.id in balances
    assert balances[bob.id]["balance"] == pytest.approx(-50.0)


@pytest.mark.asyncio
async def test_settlement_pending_expenses_no_shares_excluded_from_settled_total(
    auth_headers,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")

    members = []
    expenses = [
        {
            "name": "Unsplit",
            "value": 30,
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    data, _ = await get_settlement(headers, group_id)

    assert data["settled_total"] == pytest.approx(0.0)
    assert data["pending_total"] == pytest.approx(30.0)
    assert len(data["pending_expenses"]) == 1


@pytest.mark.asyncio
async def test_settlement_repayment_exact(
    auth_headers,
    create_user,
    add_repayment,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    # Alice created the expense so she was also the payee (fallback to the creator)
    # That means: Bob should repay Alice his share

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    # Exact repayment: Bob paid Alice 25
    await add_repayment(
        group_id,
        from_user_id=bob.id,
        to_user_id=user.id,
        amount=25,
        created_by_id=user.id,
    )

    data, balances = await get_settlement(headers, group_id)

    assert len(data["transactions"]) == 0
    assert user.id in balances
    assert bob.id in balances
    assert balances[user.id]["received"] == pytest.approx(25.0)
    assert balances[bob.id]["sent"] == pytest.approx(25.0)
    assert balances[user.id]["balance"] == pytest.approx(0.0)
    assert balances[bob.id]["balance"] == pytest.approx(0.0)
    assert data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_settlement_repayment_partial(
    auth_headers,
    create_user,
    add_repayment,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    # Alice created the expense so she was also the payee (fallback to the creator)
    # That means: Bob should repay Alice his share - 25

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    # Partial repayment: Bob paid Alice 10 (partially, still owes 15)
    await add_repayment(
        group_id,
        from_user_id=bob.id,
        to_user_id=user.id,
        amount=10,
        created_by_id=user.id,
    )

    data, balances = await get_settlement(headers, group_id)

    assert len(data["transactions"]) == 1
    assert data["transactions"] == [
        {"from_user_id": bob.id, "to_user_id": user.id, "amount": pytest.approx(15.0)}
    ]
    assert user.id in balances
    assert bob.id in balances
    assert balances[user.id]["received"] == pytest.approx(10.0)
    assert balances[bob.id]["sent"] == pytest.approx(10.0)
    assert balances[user.id]["balance"] == pytest.approx(15.0)
    assert balances[bob.id]["balance"] == pytest.approx(-15.0)
    assert data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_settlement_repayment_over(
    auth_headers,
    create_user,
    add_repayment,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    # Alice created the expense so she was also the payee (fallback to the creator)
    # That means: Bob should repay Alice his share - 25

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    # Over repayment: Bob paid Alice 50 (over-paid, Alice should pay Bob back 25)
    await add_repayment(
        group_id,
        from_user_id=bob.id,
        to_user_id=user.id,
        amount=50,
        created_by_id=user.id,
    )

    data, balances = await get_settlement(headers, group_id)

    assert len(data["transactions"]) == 1
    assert data["transactions"] == [
        {"from_user_id": user.id, "to_user_id": bob.id, "amount": pytest.approx(25.0)}
    ]
    assert user.id in balances
    assert bob.id in balances
    assert balances[user.id]["received"] == pytest.approx(50.0)
    assert balances[bob.id]["sent"] == pytest.approx(50.0)
    assert balances[user.id]["balance"] == pytest.approx(-25.0)
    assert balances[bob.id]["balance"] == pytest.approx(25.0)
    assert data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_settlement_repayment_soft_delete(
    auth_headers,
    create_user,
    add_repayment,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    # Alice created the expense so she was also the payee (fallback to the creator)
    # That means: Bob should repay Alice his share - 25

    members = [{"id": bob.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    # Soft-deleted repayment: Bob paid Alice 25, but the entry is deleted (is_deleted=True)
    await add_repayment(
        group_id,
        from_user_id=bob.id,
        to_user_id=user.id,
        amount=25,
        created_by_id=user.id,
        is_deleted=True,
        deleted_at=utcnow(),
    )

    data, balances = await get_settlement(headers, group_id)

    assert len(data["transactions"]) == 1
    assert data["transactions"] == [
        {"from_user_id": bob.id, "to_user_id": user.id, "amount": pytest.approx(25.0)}
    ]
    assert user.id in balances
    assert bob.id in balances
    assert balances[user.id]["received"] == pytest.approx(0.0)
    assert balances[bob.id]["sent"] == pytest.approx(0.0)
    assert balances[user.id]["balance"] == pytest.approx(25.0)
    assert balances[bob.id]["balance"] == pytest.approx(-25.0)
    assert data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_settlement_repayment_former_member(
    client,
    auth_headers,
    create_user,
    add_repayment,
    set_up_group_with_members_and_expenses,
    get_settlement,
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    # Alice created the expense so she was also the payee (fallback to the creator)
    # That means: Bob and John should repay Alice their shares - 20
    # John was a former member

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 60,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 3},
                {"user_id": bob.id, "ratio": 1 / 3},
                {"user_id": john.id, "ratio": 1 / 3},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        headers, group_name="Trip", members=members, expenses=expenses
    )

    # John paid Alice 20 when he was in the group
    await add_repayment(
        group_id,
        from_user_id=john.id,
        to_user_id=user.id,
        amount=20,
        created_by_id=user.id,
    )

    # Remove John from the group
    remove_response = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={john.id}",
        headers=headers,
    )
    assert remove_response.status_code == 200

    data, balances = await get_settlement(headers, group_id)

    # There is only one transaction there (Bob owes Alice)
    assert len(data["transactions"]) == 1
    assert data["transactions"] == [
        {"from_user_id": bob.id, "to_user_id": user.id, "amount": pytest.approx(20.0)}
    ]
    assert user.id in balances
    assert bob.id in balances

    # John is still included in the balances
    assert john.id in balances
    assert balances[user.id]["received"] == pytest.approx(20.0)
    assert balances[bob.id]["sent"] == pytest.approx(0.0)
    assert balances[john.id]["sent"] == pytest.approx(20.0)
    assert balances[user.id]["balance"] == pytest.approx(20)
    assert balances[bob.id]["balance"] == pytest.approx(-20.0)
    assert balances[john.id]["balance"] == pytest.approx(0.0)
    assert data["imbalance"] == pytest.approx(0.0)
