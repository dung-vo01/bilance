from typing import Any

import pytest_asyncio


@pytest_asyncio.fixture
async def set_up_group_with_members_and_expenses(client):
    async def _set_up_group_with_members_and_expenses(
        headers: dict[str, str],
        group_name: str,
        members: list[dict[str, Any]],
        expenses: list[dict[str, Any]],
    ) -> int:
        group_resp = await client.post(
            "/api/expense-groups",
            headers=headers,
            json={
                "name": group_name,
                "members": members,
            },
        )
        assert group_resp.status_code == 201, group_resp.text

        group_id = group_resp.json()["data"]["id"]

        for expense_payload in expenses:
            resp = await client.post(
                "/api/expenses",
                headers=headers,
                json={
                    **expense_payload,
                    "expense_group_id": group_id,
                },
            )
            assert resp.status_code == 201, resp.text

        return group_id

    return _set_up_group_with_members_and_expenses


@pytest_asyncio.fixture
async def get_settlement(client):
    async def _get_settlement(headers: dict[str, str], group_id: int):
        resp = await client.get(
            f"/api/expense-groups/{group_id}/settlement", headers=headers
        )
        assert resp.status_code == 200, resp.text

        data = resp.json()["data"]

        return data, {m["user_id"]: m for m in data["members"]}

    return _get_settlement


@pytest_asyncio.fixture
async def create_repayment(client):
    async def _create_repayment(
        headers,
        group_id: int,
        repayment_payload: dict[str, Any],
        expected_status: int = 201,
    ):
        resp = await client.post(
            f"/api/expense-groups/{group_id}/repayments",
            headers=headers,
            json=repayment_payload,
        )
        assert resp.status_code == expected_status, resp.text

        body = resp.json()
        return body["data"] if resp.status_code < 400 else body

    return _create_repayment
