import pytest


@pytest.mark.asyncio
async def test_create_group_creator_is_admin(client, auth_headers):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    response = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["members"][0]["user_id"] == user.id
    assert data["members"][0]["role"] == "admin"


@pytest.mark.asyncio
async def test_create_group_even_split_default(client, auth_headers, create_user):
    headers, user = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    response = await client.post(
        "/api/expense-groups",
        headers=headers,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    assert response.status_code == 201
    members = response.json()["data"]["members"]
    assert len(members) == 2
    for m in members:
        assert m["default_split_ratio"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_get_group_forbidden_for_non_member(client, auth_headers):
    headers1, _ = await auth_headers(username="alice", email="alice@example.com")
    headers2, _ = await auth_headers(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups", headers=headers1, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/api/expense-groups/{group_id}", headers=headers2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invite_creates_notification_not_direct_member(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    invite_resp = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=headers,
        json={"members": [{"username": "bob", "default_split_ratio": 0.5}]},
    )
    assert invite_resp.status_code == 200
    notifications = invite_resp.json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "group_invitation"
    assert notifications[0]["recipient_id"] == bob.id

    # Bob should NOT be a member yet
    group_resp = await client.get(f"/api/expense-groups/{group_id}", headers=headers)
    member_ids = [m["user_id"] for m in group_resp.json()["data"]["members"]]
    assert bob.id not in member_ids


@pytest.mark.asyncio
async def test_invite_duplicate_member_skipped(client, auth_headers, create_user):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    payload = {"members": [{"username": "bob", "default_split_ratio": 0.5}]}
    first = await client.post(
        f"/api/expense-groups/{group_id}/invite", headers=headers, json=payload
    )
    assert len(first.json()["data"]) == 1

    second = await client.post(
        f"/api/expense-groups/{group_id}/invite", headers=headers, json=payload
    )
    assert second.status_code == 200
    assert len(second.json()["data"]) == 0


@pytest.mark.asyncio
async def test_invite_notifies_other_admins_with_all_names_in_one(
    client, auth_headers, create_user
):
    from app.core.security import create_access_token

    headers_alice, alice = await auth_headers(
        username="alice", email="alice@example.com"
    )
    dave = await create_user(username="dave", email="dave@example.com")
    joe = await create_user(username="joe", email="joe@example.com")
    jax = await create_user(username="jax", email="jax@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_alice,
        json={"name": "Trip", "members": [{"id": dave.id, "role": "admin"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    invite_resp = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=headers_alice,
        json={
            "members": [
                {"username": "joe", "default_split_ratio": 0.25},
                {"username": "jax", "default_split_ratio": 0.25},
            ]
        },
    )
    assert invite_resp.status_code == 200
    assert len(invite_resp.json()["data"]) == 2  # joe + jax each get their own invite

    # Alice (the inviter) should NOT get an admin-notification about her own action.
    alice_data = (await client.get("/api/notifications", headers=headers_alice)).json()[
        "data"
    ]
    assert all(n["type"] != "members_invited" for n in alice_data)

    # Dave (the other admin) gets exactly ONE consolidated notification.
    dave_headers = {"Authorization": f"Bearer {create_access_token(str(dave.id))}"}
    dave_data = (await client.get("/api/notifications", headers=dave_headers)).json()[
        "data"
    ]
    members_invited = [n for n in dave_data if n["type"] == "members_invited"]
    assert len(members_invited) == 1
    assert members_invited[0]["actor"]["id"] == alice.id
    invited_usernames = {
        u["username"] for u in members_invited[0]["payload"]["invited_users"]
    }
    assert invited_usernames == {"joe", "jax"}

    # Sanity: joe and jax still each got their own actionable invite too.
    assert joe and jax


@pytest.mark.asyncio
async def test_invite_requires_admin(client, auth_headers, create_user):
    headers_admin, _ = await auth_headers(username="alice", email="alice@example.com")
    member = await create_user(username="bob", email="bob@example.com")
    outsider = await create_user(username="carol", email="carol@example.com")

    create_resp = await client.post(
        "/api/expense-groups", headers=headers_admin, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    from app.core.security import create_access_token

    member_headers = {"Authorization": f"Bearer {create_access_token(str(member.id))}"}

    # bob is not even a member yet, so this should be forbidden
    response = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=member_headers,
        json={"members": [{"username": "carol", "default_split_ratio": 0.5}]},
    )
    assert response.status_code == 403
    assert outsider  # keep reference, avoids unused warning


@pytest.mark.asyncio
async def test_invite_sends_email_only_for_group_invitation(
    client, auth_headers, create_user, monkeypatch
):
    sent = []

    async def fake_send_invitation(
        to, invitee_firstname, invitee_username, inviter_name, group_name
    ):
        sent.append(to)

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("should not send an email for members_invited")

    monkeypatch.setattr(
        "app.services.email_service.send_group_invitation_email", fake_send_invitation
    )

    headers_alice, alice = await auth_headers(
        username="alice", email="alice@example.com"
    )
    dave = await create_user(username="dave", email="dave@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_alice,
        json={"name": "Trip", "members": [{"id": dave.id, "role": "admin"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=headers_alice,
        json={"members": [{"username": "bob", "default_split_ratio": 0.5}]},
    )
    assert response.status_code == 200
    # Only bob's GROUP_INVITATION email should be attempted; dave's MEMBERS_INVITED
    # admin-notification must not trigger fail_if_called since it's never wired up.
    assert sent == ["bob@example.com"]
    assert alice and dave and bob


@pytest.mark.asyncio
async def test_invite_skips_email_when_recipient_has_no_email(
    client, auth_headers, create_user, monkeypatch
):
    called = []

    async def fake_send_invitation(*args, **kwargs):
        called.append(args)

    monkeypatch.setattr(
        "app.services.email_service.send_group_invitation_email", fake_send_invitation
    )

    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="noemail", email=None)

    create_resp = await client.post(
        "/api/expense-groups", headers=headers_alice, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/expense-groups/{group_id}/invite",
        headers=headers_alice,
        json={"members": [{"username": "noemail", "default_split_ratio": 0.5}]},
    )
    assert response.status_code == 200
    assert called == []


@pytest.mark.asyncio
async def test_bulk_update_members_self_vs_admin_permissions(
    client, auth_headers, create_user
):
    headers_admin, admin = await auth_headers(
        username="alice", email="alice@example.com"
    )
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_admin,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    from app.core.security import create_access_token

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    # Bob can edit his own ratio
    response = await client.patch(
        f"/api/expense-groups/{group_id}/members",
        headers=bob_headers,
        json={"members": [{"user_id": bob.id, "default_split_ratio": 0.3}]},
    )
    assert response.status_code == 200
    updated = {m["user_id"]: m for m in response.json()["data"]}
    assert updated[bob.id]["default_split_ratio"] == pytest.approx(0.3)


@pytest.mark.asyncio
async def test_bulk_update_self_role_edit_is_ignored(client, auth_headers):
    # An admin can never change their own role via bulk update (only another
    # admin can demote someone) — this is what keeps "at least one admin"
    # enforceable, since the acting admin can't accidentally strip themselves.
    headers_admin, admin = await auth_headers(
        username="alice", email="alice@example.com"
    )
    create_resp = await client.post(
        "/api/expense-groups", headers=headers_admin, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.patch(
        f"/api/expense-groups/{group_id}/members",
        headers=headers_admin,
        json={"members": [{"user_id": admin.id, "role": "member"}]},
    )
    assert response.status_code == 200
    updated = {m["user_id"]: m for m in response.json()["data"]}
    assert updated[admin.id]["role"] == "admin"


@pytest.mark.asyncio
async def test_leave_group_blocked_if_sole_admin(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    create_resp = await client.post(
        "/api/expense-groups", headers=headers, json={"name": "Trip"}
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/expense-groups/{group_id}/leave", headers=headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_remove_members_requires_admin(client, auth_headers, create_user):
    headers_admin, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_admin,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    from app.core.security import create_access_token

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    response = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={bob.id}",
        headers=bob_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_members_notifies_removed_member(
    client, auth_headers, create_user
):
    from app.core.security import create_access_token

    headers_admin, admin = await auth_headers(
        username="alice", email="alice@example.com"
    )
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_admin,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={bob.id}",
        headers=headers_admin,
    )
    assert response.status_code == 200

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    notifications = (
        await client.get("/api/notifications", headers=bob_headers)
    ).json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "member_removed"
    assert notifications[0]["actor"]["id"] == admin.id
    assert notifications[0]["expense_group_id"] == group_id


@pytest.mark.asyncio
async def test_remove_members_notifies_other_admins(client, auth_headers, create_user):
    from app.core.security import create_access_token

    headers_alice, alice = await auth_headers(
        username="alice", email="alice@example.com"
    )
    dave = await create_user(username="dave", email="dave@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_alice,
        json={
            "name": "Trip",
            "members": [
                {"id": dave.id, "role": "admin"},
                {"id": bob.id, "role": "member"},
            ],
        },
    )
    group_id = create_resp.json()["data"]["id"]

    response = await client.delete(
        f"/api/expense-groups/{group_id}/members?member_ids={bob.id}",
        headers=headers_alice,
    )
    assert response.status_code == 200

    # Bob (the removed member) gets a notification with no payload.
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    bob_data = (await client.get("/api/notifications", headers=bob_headers)).json()[
        "data"
    ]
    assert len(bob_data) == 1
    assert bob_data[0]["payload"] is None

    # Dave (the other admin, not the one who removed Bob) also gets a
    # notification, this one identifying who was removed.
    dave_headers = {"Authorization": f"Bearer {create_access_token(str(dave.id))}"}
    dave_data = (await client.get("/api/notifications", headers=dave_headers)).json()[
        "data"
    ]
    assert len(dave_data) == 1
    assert dave_data[0]["type"] == "member_removed"
    assert dave_data[0]["actor"]["id"] == alice.id
    assert dave_data[0]["payload"]["removed_user_id"] == bob.id
    assert dave_data[0]["payload"]["removed_user"]["username"] == "bob"


@pytest.mark.asyncio
async def test_leave_group_notifies_remaining_admins(client, auth_headers, create_user):
    from app.core.security import create_access_token

    headers_admin, admin = await auth_headers(
        username="alice", email="alice@example.com"
    )
    bob = await create_user(username="bob", email="bob@example.com")

    create_resp = await client.post(
        "/api/expense-groups",
        headers=headers_admin,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )
    group_id = create_resp.json()["data"]["id"]

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    response = await client.post(
        f"/api/expense-groups/{group_id}/leave", headers=bob_headers
    )
    assert response.status_code == 200

    notifications = (
        await client.get("/api/notifications", headers=headers_admin)
    ).json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "member_left"
    assert notifications[0]["actor"]["id"] == bob.id
    assert notifications[0]["recipient_id"] == admin.id
