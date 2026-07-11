from datetime import datetime, timedelta, timezone

import pytest


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


async def _create_category(client, headers, name: str) -> int:
    resp = await client.post(
        "/api/categories", headers=headers, json={"name": name, "description": ""}
    )
    return resp.json()["data"]["id"]


async def _create_expense(
    client, headers, *, value, days_ago=None, category_id=None, expense_group_id=None
):
    payload = {"name": "Expense", "value": value}
    if days_ago is not None:
        payload["paid_at"] = _days_ago(days_ago)
    if category_id is not None:
        payload["category_id"] = category_id
    if expense_group_id is not None:
        payload["expense_group_id"] = expense_group_id
    resp = await client.post("/api/expenses", headers=headers, json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_category_breakdown_respects_the_time_window(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    groceries = await _create_category(client, headers, "Groceries")

    await _create_expense(client, headers, value=10, days_ago=3, category_id=groceries)
    await _create_expense(client, headers, value=20, days_ago=20, category_id=groceries)
    await _create_expense(client, headers, value=40, days_ago=90, category_id=groceries)

    resp_7d = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 7}
    )
    data_7d = resp_7d.json()["data"]
    assert data_7d["total"] == pytest.approx(10.0)

    resp_30d = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 30}
    )
    data_30d = resp_30d.json()["data"]
    assert data_30d["total"] == pytest.approx(30.0)


@pytest.mark.asyncio
async def test_category_breakdown_groups_by_category_with_percentages(
    client, auth_headers
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    groceries = await _create_category(client, headers, "Groceries")
    dining = await _create_category(client, headers, "Dining")

    await _create_expense(client, headers, value=75, days_ago=1, category_id=groceries)
    await _create_expense(client, headers, value=25, days_ago=1, category_id=dining)

    resp = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 30}
    )
    data = resp.json()["data"]
    assert data["total"] == pytest.approx(100.0)

    by_name = {c["category_name"]: c for c in data["categories"]}
    assert by_name["Groceries"]["total"] == pytest.approx(75.0)
    assert by_name["Groceries"]["percentage"] == pytest.approx(75.0)
    assert by_name["Dining"]["total"] == pytest.approx(25.0)
    assert by_name["Dining"]["percentage"] == pytest.approx(25.0)


@pytest.mark.asyncio
async def test_category_breakdown_labels_uncategorized_expenses(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    await _create_expense(client, headers, value=15, days_ago=1)

    resp = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 30}
    )
    categories = resp.json()["data"]["categories"]
    assert len(categories) == 1
    assert categories[0]["category_name"] == "No category"
    assert categories[0]["category_id"] is None


@pytest.mark.asyncio
async def test_category_breakdown_excludes_group_and_deleted_expenses(
    client, auth_headers
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")

    group_resp = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    group_id = group_resp.json()["data"]["id"]
    await _create_expense(
        client, headers, value=500, days_ago=1, expense_group_id=group_id
    )

    deleted_id = await _create_expense(client, headers, value=999, days_ago=1)
    await client.delete(f"/api/expenses/{deleted_id}", headers=headers)

    await _create_expense(client, headers, value=5, days_ago=1)

    resp = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 30}
    )
    data = resp.json()["data"]
    assert data["total"] == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_category_breakdown_excludes_expenses_without_paid_at(
    client, auth_headers
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    await _create_expense(client, headers, value=50)  # no paid_at

    resp = await client.get(
        "/api/expenses/category-breakdown", headers=headers, params={"days": 30}
    )
    data = resp.json()["data"]
    assert data["total"] == 0
    assert data["categories"] == []


@pytest.mark.asyncio
async def test_category_breakdown_scoped_to_group_includes_all_members(
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
    groceries = await _create_category(client, headers, "Groceries")

    await _create_expense(
        client,
        headers,
        value=30,
        days_ago=1,
        category_id=groceries,
        expense_group_id=group_id,
    )
    # bob's own header isn't available here, but payee_id can be set explicitly
    resp = await client.post(
        "/api/expenses",
        headers=headers,
        json={
            "name": "Bob's share",
            "value": 20,
            "category_id": groceries,
            "expense_group_id": group_id,
            "payee_id": bob.id,
            "paid_at": _days_ago(1),
        },
    )
    assert resp.status_code == 201

    # a personal expense for alice that must NOT leak into the group total
    await _create_expense(client, headers, value=999, days_ago=1, category_id=groceries)

    resp = await client.get(
        "/api/expenses/category-breakdown",
        headers=headers,
        params={"days": 30, "expense_group_id": group_id},
    )
    data = resp.json()["data"]
    assert data["total"] == pytest.approx(50.0)
    assert len(data["categories"]) == 1
    assert data["categories"][0]["category_name"] == "Groceries"


@pytest.mark.asyncio
async def test_category_breakdown_non_member_cannot_view_group_breakdown(
    client, auth_headers
):
    headers_owner, _ = await auth_headers(username="alice", email="alice@example.com")
    headers_outsider, _ = await auth_headers(username="bob", email="bob@example.com")

    group_resp = await client.post(
        "/api/expense-groups", headers=headers_owner, json={"name": "Trip"}
    )
    group_id = group_resp.json()["data"]["id"]

    resp = await client.get(
        "/api/expenses/category-breakdown",
        headers=headers_outsider,
        params={"days": 30, "expense_group_id": group_id},
    )
    assert resp.status_code == 403
