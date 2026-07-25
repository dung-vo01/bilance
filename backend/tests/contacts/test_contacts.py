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


async def _become_contacts(client, headers_a, headers_b, other_username):
    """Send a request from a -> b (by b's username) and accept it as b."""
    await client.post(
        "/api/contacts/requests", headers=headers_a, json={"username": other_username}
    )
    notification_id = (
        await client.get("/api/notifications", headers=headers_b)
    ).json()["data"][0]["id"]
    await client.post(
        f"/api/notifications/contacts/{notification_id}/respond",
        headers=headers_b,
        json={"accept": True},
    )


@pytest.mark.asyncio
async def test_contacts_detail_includes_shared_groups(
    client, auth_headers, create_user
):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await _become_contacts(client, headers_alice, bob_headers, "bob")

    await client.post(
        "/api/expense-groups",
        headers=headers_alice,
        json={"name": "Trip", "members": [{"id": bob.id, "role": "member"}]},
    )

    detail = (await client.get("/api/contacts/detail", headers=headers_alice)).json()[
        "data"
    ]
    bob_detail = next(c for c in detail if c["username"] == "bob")
    assert bob_detail["email"] == "bob@example.com"
    assert any(g["name"] == "Trip" for g in bob_detail["shared_groups"])


@pytest.mark.asyncio
async def test_contacts_detail_empty_shared_groups_when_none(
    client, auth_headers, create_user
):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await _become_contacts(client, headers_alice, bob_headers, "bob")

    detail = (await client.get("/api/contacts/detail", headers=headers_alice)).json()[
        "data"
    ]
    bob_detail = next(c for c in detail if c["username"] == "bob")
    assert bob_detail["shared_groups"] == []


@pytest.mark.asyncio
async def test_remove_contact_deletes_both_directions(
    client, auth_headers, create_user
):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await _become_contacts(client, headers_alice, bob_headers, "bob")

    remove_resp = await client.delete(f"/api/contacts/{bob.id}", headers=headers_alice)
    assert remove_resp.status_code == 200

    alice_detail = (
        await client.get("/api/contacts/detail", headers=headers_alice)
    ).json()["data"]
    assert not any(c["username"] == "bob" for c in alice_detail)

    bob_detail = (await client.get("/api/contacts/detail", headers=bob_headers)).json()[
        "data"
    ]
    assert not any(c["username"] == "alice" for c in bob_detail)


@pytest.mark.asyncio
async def test_remove_contact_404_for_non_contact(client, auth_headers, create_user):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")

    response = await client.delete(f"/api/contacts/{bob.id}", headers=headers_alice)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sent_requests_lists_pending_and_excludes_resolved(
    client, auth_headers, create_user
):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    dave = await create_user(username="dave", email="dave@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await client.post(
        "/api/contacts/requests", headers=headers_alice, json={"username": "dave"}
    )
    await _become_contacts(client, headers_alice, bob_headers, "bob")

    sent = (
        await client.get("/api/contacts/requests/sent", headers=headers_alice)
    ).json()["data"]
    assert len(sent) == 1
    assert sent[0]["recipient"]["username"] == "dave"
    assert dave.id


@pytest.mark.asyncio
async def test_cancel_request_removes_it(client, auth_headers, create_user):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="bob", email="bob@example.com")

    await client.post(
        "/api/contacts/requests", headers=headers_alice, json={"username": "bob"}
    )

    sent = (
        await client.get("/api/contacts/requests/sent", headers=headers_alice)
    ).json()["data"]
    request_id = sent[0]["id"]

    cancel_resp = await client.delete(
        f"/api/contacts/requests/{request_id}", headers=headers_alice
    )
    assert cancel_resp.status_code == 200

    second_cancel = await client.delete(
        f"/api/contacts/requests/{request_id}", headers=headers_alice
    )
    assert second_cancel.status_code == 404


@pytest.mark.asyncio
async def test_cancel_request_forbidden_for_wrong_user(
    client, auth_headers, create_user
):
    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await client.post(
        "/api/contacts/requests", headers=headers_alice, json={"username": "bob"}
    )
    sent = (
        await client.get("/api/contacts/requests/sent", headers=headers_alice)
    ).json()["data"]
    request_id = sent[0]["id"]

    response = await client.delete(
        f"/api/contacts/requests/{request_id}", headers=bob_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_send_contact_request_triggers_email(
    client, auth_headers, create_user, monkeypatch
):
    sent = []

    async def fake_send(to, recipient_firstname, recipient_username, requester_name):
        sent.append(to)

    monkeypatch.setattr(
        "app.services.email_service.send_contact_request_email", fake_send
    )

    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    await create_user(username="bob", email="bob@example.com")

    response = await client.post(
        "/api/contacts/requests", headers=headers_alice, json={"username": "bob"}
    )
    assert response.status_code == 201
    assert sent == ["bob@example.com"]


@pytest.mark.asyncio
async def test_respond_contact_request_does_not_trigger_email(
    client, auth_headers, create_user, monkeypatch
):
    called = []

    async def fail_if_called(*args, **kwargs):
        called.append(args)

    async def fake_send_request(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.services.email_service.send_contact_request_email", fake_send_request
    )

    headers_alice, _ = await auth_headers(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    bob_headers = {"Authorization": f"Bearer {create_access_token(str(bob.id))}"}

    await client.post(
        "/api/contacts/requests", headers=headers_alice, json={"username": "bob"}
    )
    notification_id = (
        await client.get("/api/notifications", headers=bob_headers)
    ).json()["data"][0]["id"]

    # Swap in a failing stub only for the respond step, to prove it's never called.
    monkeypatch.setattr(
        "app.services.email_service.send_contact_request_email", fail_if_called
    )

    respond = await client.post(
        f"/api/notifications/contacts/{notification_id}/respond",
        headers=bob_headers,
        json={"accept": True},
    )
    assert respond.status_code == 200
    assert called == []
