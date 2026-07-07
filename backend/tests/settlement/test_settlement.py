import pytest


@pytest.mark.asyncio
async def test_settlement_balances_paid_minus_owed(client, auth_headers, create_user):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    group_resp = await client.post(
        "/api/expense-groups",
        headers=headers,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = group_resp.json()["data"]["id"]

    await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Dinner",
            "value": 100,
            "expense_group_id": group_id,
            "shares": [
                {"user_id": user.id, "ratio": 0.6},
                {"user_id": bob.id, "ratio": 0.4},
            ],
        },
    )

    response = await client.get(
        f"/api/expense-groups/{group_id}/settlement", headers=headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    balances = {m["user_id"]: m for m in data["members"]}
    assert balances[user.id]["balance"] == pytest.approx(40.0)
    assert balances[bob.id]["balance"] == pytest.approx(-40.0)


@pytest.mark.asyncio
async def test_settlement_debt_simplification_transactions(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    carol = await create_user(username="carol", email="carol@example.com")

    group_resp = await client.post(
        "/api/expense-groups",
        headers=headers,
        json={
            "name": "Trip",
            "members": [
                {"id": bob.id, "role": "member"},
                {"id": carol.id, "role": "member"},
            ],
        },
    )
    group_id = group_resp.json()["data"]["id"]

    await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Hotel",
            "value": 90,
            "expense_group_id": group_id,
            "shares": [
                {"user_id": user.id, "ratio": 1 / 3},
                {"user_id": bob.id, "ratio": 1 / 3},
                {"user_id": carol.id, "ratio": 1 / 3},
            ],
        },
    )

    response = await client.get(
        f"/api/expense-groups/{group_id}/settlement", headers=headers
    )
    data = response.json()["data"]
    total_transacted = sum(t["amount"] for t in data["transactions"])
    assert total_transacted == pytest.approx(60.0)
    for txn in data["transactions"]:
        assert txn["to_user_id"] == user.id


@pytest.mark.asyncio
async def test_settlement_former_member_shares_still_counted(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    group_resp = await client.post(
        "/api/expense-groups",
        headers=headers,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = group_resp.json()["data"]["id"]

    await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Dinner",
            "value": 100,
            "expense_group_id": group_id,
            "shares": [
                {"user_id": user.id, "ratio": 0.5},
                {"user_id": bob.id, "ratio": 0.5},
            ],
        },
    )

    remove_resp = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={bob.id}", headers=headers
    )
    assert remove_resp.status_code == 200

    response = await client.get(
        f"/api/expense-groups/{group_id}/settlement", headers=headers
    )
    data = response.json()["data"]
    balances = {m["user_id"]: m for m in data["members"]}
    assert bob.id in balances
    assert balances[bob.id]["balance"] == pytest.approx(-50.0)


@pytest.mark.asyncio
async def test_settlement_pending_expenses_no_shares_excluded_from_settled_total(
    client, auth_headers
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    group_resp = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    group_id = group_resp.json()["data"]["id"]

    await client.post(
        "/api/expenses",
        headers=headers,
        json={"name": "Unsplit", "value": 30, "expense_group_id": group_id},
    )

    response = await client.get(
        f"/api/expense-groups/{group_id}/settlement", headers=headers
    )
    data = response.json()["data"]
    assert data["settled_total"] == pytest.approx(0.0)
    assert data["pending_total"] == pytest.approx(30.0)
    assert len(data["pending_expenses"]) == 1
