import pytest
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_send_contact_request_creates_notification(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    response = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "bob"}
    )
    assert response.status_code == 201

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    notifications = (
        await client.get("/api/notifications", headers=bob_headers)
    ).json()["data"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "contact_request"


@pytest.mark.asyncio
async def test_send_contact_request_unknown_username(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    response = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "nobody"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_contact_request_to_self(client, auth_headers):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    response = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "alice"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_send_contact_request_duplicate_pending(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="bob", email="bob@example.com")

    first = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "bob"}
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "bob"}
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_respond_contact_request_accept_creates_symmetric_contacts(
    client, auth_headers, create_user
):
    headers, alice = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    send_resp = await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "bob"}
    )
    assert send_resp.status_code == 201

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    notification_id = (
        await client.get("/api/notifications", headers=bob_headers)
    ).json()["data"][0]["id"]

    respond = await client.post(
        f"/api/notifications/contacts/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert respond.status_code == 200

    alice_contacts = (await client.get("/api/contacts", headers=headers)).json()["data"]
    assert any(c["username"] == "bob" for c in alice_contacts)

    bob_contacts = (await client.get("/api/contacts", headers=bob_headers)).json()[
        "data"
    ]
    assert any(c["username"] == "alice" for c in bob_contacts)

    # Alice should have gotten a contact_accepted notification back
    alice_notifications = (
        await client.get("/api/notifications", headers=headers)
    ).json()["data"]
    assert any(n["type"] == "contact_accepted" for n in alice_notifications)
    assert alice.id  # keep reference


@pytest.mark.asyncio
async def test_respond_contact_request_decline_does_not_create_contact(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    await client.post(
        "/api/contacts/requests", headers=headers, json={"username": "bob"}
    )

    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}
    notification_id = (
        await client.get("/api/notifications", headers=bob_headers)
    ).json()["data"][0]["id"]

    respond = await client.post(
        f"/api/notifications/contacts/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": False},
    )
    assert respond.status_code == 200

    alice_contacts = (await client.get("/api/contacts", headers=headers)).json()["data"]
    assert not any(c["username"] == "bob" for c in alice_contacts)


@pytest.mark.asyncio
async def test_get_visible_contacts_includes_shared_group_members(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    await client.post(
        "/api/expense-groups",
        headers=headers,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )

    contacts = (await client.get("/api/contacts", headers=headers)).json()["data"]
    assert any(c["username"] == "bob" for c in contacts)


@pytest.mark.asyncio
async def test_get_visible_contacts_excludes_strangers(
    client, auth_headers, create_user
):
    headers, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="stranger", email="stranger@example.com")

    contacts = (await client.get("/api/contacts", headers=headers)).json()["data"]
    assert not any(c["username"] == "stranger" for c in contacts)
