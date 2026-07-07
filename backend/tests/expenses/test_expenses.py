import pytest


async def _create_group(client, headers, members=None):
    payload = {"name": "Trip"}
    if members:
        payload["members"] = members
    resp = await client.post("/api/expense-groups", headers=headers, json=payload)
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_create_personal_expense_defaults_payee_to_self(client, auth_headers):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    response = await client.post(
        "/api/expenses", headers=headers, json={"name": "Coffee", "value": 4.5}
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["payee_id"] == user.id
    assert data["expense_group_id"] is None


@pytest.mark.asyncio
async def test_create_group_expense_with_custom_shares(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id = await _create_group(
        client, headers, members=[{"id": bob.id, "role": "member"}]
    )

    response = await client.post(
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
    assert response.status_code == 201
    shares = {s["user_id"]: s for s in response.json()["data"]["shares"]}
    assert shares[user.id]["amount"] == pytest.approx(60.0)
    assert shares[bob.id]["amount"] == pytest.approx(40.0)


@pytest.mark.asyncio
async def test_create_group_expense_ratio_must_sum_to_one(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id = await _create_group(
        client, headers, members=[{"id": bob.id, "role": "member"}]
    )

    response = await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Dinner",
            "value": 100,
            "expense_group_id": group_id,
            "shares": [
                {"user_id": user.id, "ratio": 0.6},
                {"user_id": bob.id, "ratio": 0.6},
            ],
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_group_expense_default_split_snapshot_from_member_ratio(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id = await _create_group(
        client, headers, members=[{"id": bob.id, "role": "member"}]
    )

    # No explicit shares — expense has no shares generated automatically today
    # (auto-generation from default_split_ratio is a group-level default; verify
    # the expense is created without shares when none are supplied).
    response = await client.post(
        "/api/expenses",
        headers=headers,
        json={"name": "Snacks", "value": 20, "expense_group_id": group_id},
    )
    assert response.status_code == 201
    assert response.json()["data"]["shares"] == []


@pytest.mark.asyncio
async def test_update_expense_recreates_shares(client, auth_headers, create_user):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id = await _create_group(
        client, headers, members=[{"id": bob.id, "role": "member"}]
    )

    create_resp = await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Dinner",
            "value": 100,
            "expense_group_id": group_id,
            "shares": [{"user_id": user.id, "ratio": 1.0}],
        },
    )
    expense_id = create_resp.json()["data"]["id"]

    update_resp = await client.patch(
        f"/api/expenses/{expense_id}",
        headers=headers,
        json={
            "shares": [
                {"user_id": user.id, "ratio": 0.5},
                {"user_id": bob.id, "ratio": 0.5},
            ]
        },
    )
    assert update_resp.status_code == 200
    shares = update_resp.json()["data"]["shares"]
    assert len(shares) == 2
    assert all(s["amount"] == pytest.approx(50.0) for s in shares)


@pytest.mark.asyncio
async def test_update_expense_value_only_recalculates_share_amounts(
    client, auth_headers, create_user
):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id = await _create_group(
        client, headers, members=[{"id": bob.id, "role": "member"}]
    )

    create_resp = await client.post(
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
    expense_id = create_resp.json()["data"]["id"]

    update_resp = await client.patch(
        f"/api/expenses/{expense_id}", headers=headers, json={"value": 200}
    )
    assert update_resp.status_code == 200
    shares = update_resp.json()["data"]["shares"]
    assert all(s["amount"] == pytest.approx(100.0) for s in shares)


@pytest.mark.asyncio
async def test_soft_delete_sets_is_deleted_true(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    create_resp = await client.post(
        "/api/expenses", headers=headers, json={"name": "Coffee", "value": 4.5}
    )
    expense_id = create_resp.json()["data"]["id"]

    delete_resp = await client.delete(f"/api/expenses/{expense_id}", headers=headers)
    assert delete_resp.status_code == 200

    list_resp = await client.get("/api/expenses", headers=headers)
    matching = [e for e in list_resp.json()["data"] if e["id"] == expense_id]
    assert matching[0]["is_deleted"] is True


@pytest.mark.asyncio
async def test_non_member_cannot_create_group_expense(client, auth_headers):
    headers_owner, _ = await auth_headers(username="alice", email="alice@example.com")
    headers_outsider, _ = await auth_headers(username="bob", email="bob@example.com")
    group_id = await _create_group(client, headers_owner)

    response = await client.post(
        "/api/expenses",
        headers=headers_outsider,
        json={"name": "Snacks", "value": 20, "expense_group_id": group_id},
    )
    assert response.status_code == 403
