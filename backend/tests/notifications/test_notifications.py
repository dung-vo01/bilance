import pytest
from app.core.security import create_access_token


async def _create_group_and_invite(client, admin_headers, invitee_username, ratio=0.5):
    group_resp = await client.post(
        "/api/expense-groups", headers=admin_headers, json={"name": "Trip"}
    )
    group_id = group_resp.json()["data"]["id"]
    invite_resp = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=admin_headers,
        json={
            "members": [{"username": invitee_username, "default_split_ratio": ratio}]
        },
    )
    notification_id = invite_resp.json()["data"][0]["id"]
    return group_id, notification_id


@pytest.mark.asyncio
async def test_invite_creates_unread_notification_for_invitee(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.get("/api/notifications", headers=bob_headers)
    assert response.status_code == 200
    notifications = response.json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["is_read"] is False


@pytest.mark.asyncio
async def test_list_notifications_only_returns_own_unread(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    carol = await create_user(username="carol", email="carol@example.com")
    await _create_group_and_invite(client, headers, "bob")

    carol_headers = {"Authorization": f"Bearer {create_access_token(str(carol.id))}"}
    response = await client.get("/api/notifications", headers=carol_headers)
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_mark_read_forbidden_for_other_users_notification(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    carol = await create_user(username="carol", email="carol@example.com")
    _, notification_id = await _create_group_and_invite(client, headers, "bob")

    carol_headers = {"Authorization": f"Bearer {create_access_token(str(carol.id))}"}
    response = await client.post(
        f"/api/notifications/{notification_id}/read", headers=carol_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_respond_invitation_accept_creates_membership(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id, notification_id = await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert response.status_code == 200

    group_resp = await client.get(f"/api/expense-groups/{group_id}", headers=headers)
    member_ids = [m["user_id"] for m in group_resp.json()["data"]["members"]]
    assert bob.id in member_ids


@pytest.mark.asyncio
async def test_respond_invitation_decline_does_not_create_membership(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    group_id, notification_id = await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": False},
    )
    assert response.status_code == 200

    group_resp = await client.get(f"/api/expense-groups/{group_id}", headers=headers)
    member_ids = [m["user_id"] for m in group_resp.json()["data"]["members"]]
    assert bob.id not in member_ids


@pytest.mark.asyncio
async def test_respond_invitation_accept_notifies_inviter(
    client, auth_headers, create_user
):
    headers, alice = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    _, notification_id = await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert response.status_code == 200

    alice_notifications = await client.get("/api/notifications", headers=headers)
    data = alice_notifications.json()["data"]
    assert len(data) == 1
    assert data[0]["type"] == "invitation_accepted"
    assert data[0]["actor"]["id"] == bob.id
    assert data[0]["recipient_id"] == alice.id
    assert data[0]["is_read"] is False


@pytest.mark.asyncio
async def test_respond_invitation_decline_notifies_inviter(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    _, notification_id = await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": False},
    )
    assert response.status_code == 200

    alice_notifications = await client.get("/api/notifications", headers=headers)
    data = alice_notifications.json()["data"]
    assert len(data) == 1
    assert data[0]["type"] == "invitation_declined"
    assert data[0]["actor"]["id"] == bob.id


@pytest.mark.asyncio
async def test_respond_invitation_notifies_all_current_admins(
    client, auth_headers, create_user
):
    # Alice invites Bob, but Dave is *also* an admin of the group — both
    # should hear about the outcome, not just whoever sent the invite.
    headers_alice, alice = await auth_headers(
        username="alice", email="alice@example.com"
    )
    dave = await create_user(username="dave", email="dave@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    group_resp = await client.post(
        "/api/expense-groups",
        headers=headers_alice,
        json={"name": "Trip", "members": [{"id": dave.id, "role": "admin"}]},
    )
    group_id = group_resp.json()["data"]["id"]

    invite_resp = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=headers_alice,
        json={"members": [{"username": "bob", "default_split_ratio": 0.5}]},
    )
    notification_id = invite_resp.json()["data"][0]["id"]

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert response.status_code == 200

    alice_data = (await client.get("/api/notifications", headers=headers_alice)).json()[
        "data"
    ]
    assert len(alice_data) == 1
    assert alice_data[0]["type"] == "invitation_accepted"

    dave_headers = {"Authorization": f"Bearer {create_access_token(str(dave.id))}"}
    dave_data = (await client.get("/api/notifications", headers=dave_headers)).json()[
        "data"
    ]
    # Dave also got a members_invited notification when Alice invited Bob —
    # that's the separate feature covered in test_expense_groups.py. Here we
    # only care about the invitation_accepted one.
    accepted = [n for n in dave_data if n["type"] == "invitation_accepted"]
    assert len(accepted) == 1
    assert accepted[0]["actor"]["id"] == bob.id


@pytest.mark.asyncio
async def test_respond_invitation_twice_fails_already_resolved(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    _, notification_id = await _create_group_and_invite(client, headers, "bob")

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    first = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/notifications/invitations/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert second.status_code == 400
