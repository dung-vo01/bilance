import pytest


@pytest.mark.asyncio
async def test_create_repayment_as_group_admin(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    alice = scenario.alice
    bob = scenario.bob
    john = scenario.john
    alice_headers = scenario.alice_headers
    group_id = scenario.group_id

    # Before repayment, John should owe Bob 25 (1 transaction)
    settlement_data, _ = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by group_admin (Alice)
    repayment_data = await create_repayment(alice_headers, group_id, repayment_payload)

    assert repayment_data["amount"] == pytest.approx(25.0)
    assert repayment_data["from_user"]["id"] == john.id
    assert repayment_data["to_user"]["id"] == bob.id
    assert (
        repayment_data["created_by"]["id"] == alice.id
    )  # Alice created the repayment entry
    assert repayment_data["is_deleted"] is False
    assert repayment_data["deleted_at"] is None

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 0


@pytest.mark.asyncio
async def test_create_repayment_as_to_user(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    bob_headers = scenario.bob_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    repayment_data = await create_repayment(bob_headers, group_id, repayment_payload)

    assert repayment_data["amount"] == pytest.approx(25.0)
    assert repayment_data["from_user"]["id"] == john.id
    assert repayment_data["to_user"]["id"] == bob.id
    assert (
        repayment_data["created_by"]["id"] == bob.id
    )  # Bob created the repayment entry
    assert repayment_data["is_deleted"] is False
    assert repayment_data["deleted_at"] is None

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 0


@pytest.mark.asyncio
async def test_create_repayment_as_from_user(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    john_headers = scenario.john_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }

    # Repayment created by from_user (John)
    repayment_data = await create_repayment(john_headers, group_id, repayment_payload)

    assert repayment_data["amount"] == pytest.approx(25.0)
    assert repayment_data["from_user"]["id"] == john.id
    assert repayment_data["to_user"]["id"] == bob.id
    assert (
        repayment_data["created_by"]["id"] == john.id
    )  # John created the repayment entry
    assert repayment_data["is_deleted"] is False
    assert repayment_data["deleted_at"] is None

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 0


@pytest.mark.asyncio
async def test_create_repayment_as_irrelevant_group_member(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    # Dung is a group member but not involved in the above expense
    # Dung tries to create repayment for the above expense
    scenario = bob_paid_john_owes

    john = scenario.john
    bob = scenario.bob
    dung_headers = scenario.dung_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }

    # Repayment created by a group member (Dung) who wasn't involved in the transaction
    # Expect this call to FAIL
    body = await create_repayment(
        dung_headers, group_id, repayment_payload, expected_status=403
    )

    assert "You are not allowed to create repayment" in body["error"]

    # Current settlement unchanged, there is still 1 transaction
    settlement_data, _ = await get_settlement(dung_headers, group_id)
    assert len(settlement_data["transactions"]) == 1


@pytest.mark.asyncio
async def test_create_repayment_with_stale_amount(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    john_headers = scenario.john_headers
    group_id = scenario.group_id

    # John's screen shows he owes 30 (his share of a 60 total).
    # Someone then edited the expense to 50, so he now owes 25,
    # but John didn't refresh and submits 30.
    repayment_payload = {
        "amount": 30,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Expect repayment created by John to FAIL
    body = await create_repayment(
        john_headers, group_id, repayment_payload, expected_status=409
    )

    assert "Settlement has changed, please refresh!" in body["error"]

    # Current settlement unchanged, there is still 1 transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)
    assert len(settlement_data["transactions"]) == 1


@pytest.mark.asyncio
async def test_create_repayment_duplicate(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    john_headers = scenario.john_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }

    repayment_data = await create_repayment(john_headers, group_id, repayment_payload)

    assert repayment_data["amount"] == pytest.approx(25.0)
    assert repayment_data["from_user"]["id"] == john.id
    assert repayment_data["to_user"]["id"] == bob.id
    assert (
        repayment_data["created_by"]["id"] == john.id
    )  # John created the repayment entry
    assert repayment_data["is_deleted"] is False
    assert repayment_data["deleted_at"] is None

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # HOWEVER, somehow John created the repayment again (double click), expect this time to FAIL
    body = await create_repayment(
        john_headers, group_id, repayment_payload, expected_status=409
    )

    assert "Settlement has changed, please refresh!" in body["error"]

    # Current settlement unchanged, no transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)
    assert len(settlement_data["transactions"]) == 0


@pytest.mark.asyncio
async def test_create_repayment_wrong_direction(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    john_headers = scenario.john_headers
    group_id = scenario.group_id

    # Repayment in a wrong direction: Bob paid John 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": bob.id,
        "to_user_id": john.id,
    }

    # Expect this to fail since the repayment is in wrong direction
    body = await create_repayment(
        john_headers, group_id, repayment_payload, expected_status=409
    )

    assert "Settlement has changed, please refresh!" in body["error"]

    # Current settlement unchanged, there is still 1 transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)
    assert len(settlement_data["transactions"]) == 1


@pytest.mark.asyncio
async def test_unresolve_repayment_as_group_admin(
    bob_paid_john_owes, get_settlement, create_repayment, unresolve_repayment
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    alice = scenario.alice
    bob = scenario.bob
    john = scenario.john
    alice_headers = scenario.alice_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by group_admin (Alice)
    repayment_data = await create_repayment(alice_headers, group_id, repayment_payload)

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # Then, Alice unresolved the repayment
    unresolve_payload = {"deleted_note": "Bob didn't receive his payment"}
    unresolve_data = await unresolve_repayment(
        alice_headers, group_id, repayment_data["id"], unresolve_payload
    )

    assert unresolve_data["is_deleted"] is True
    assert unresolve_data["deleted_at"] is not None
    assert unresolve_data["deleted_by"]["id"] == alice.id
    assert unresolve_data["deleted_note"] == unresolve_payload["deleted_note"]

    # After repayment getting unresolved, transaction came back with the settlement of 25
    settlement_data, _ = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.00)


@pytest.mark.asyncio
async def test_unresolve_repayment_as_from_user(
    bob_paid_john_owes, get_settlement, create_repayment, unresolve_repayment
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    john_headers = scenario.john_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by from_user (John)
    repayment_data = await create_repayment(john_headers, group_id, repayment_payload)

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # Then, John unresolved the repayment
    unresolve_payload = {"deleted_note": "Payment didn't go through"}
    unresolve_data = await unresolve_repayment(
        john_headers, group_id, repayment_data["id"], unresolve_payload
    )

    assert unresolve_data["is_deleted"] is True
    assert unresolve_data["deleted_at"] is not None
    assert unresolve_data["deleted_by"]["id"] == john.id
    assert unresolve_data["deleted_note"] == unresolve_payload["deleted_note"]

    # After repayment getting unresolved, transaction came back with the settlement of 25
    settlement_data, _ = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.00)


@pytest.mark.asyncio
async def test_unresolve_repayment_as_to_user(
    bob_paid_john_owes, get_settlement, create_repayment, unresolve_repayment
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    bob_headers = scenario.bob_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    repayment_data = await create_repayment(bob_headers, group_id, repayment_payload)

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # Then, Bob unresolved the repayment
    unresolve_payload = {"deleted_note": "I didn't receive anything"}
    unresolve_data = await unresolve_repayment(
        bob_headers, group_id, repayment_data["id"], unresolve_payload
    )

    assert unresolve_data["is_deleted"] is True
    assert unresolve_data["deleted_at"] is not None
    assert unresolve_data["deleted_by"]["id"] == bob.id
    assert unresolve_data["deleted_note"] == unresolve_payload["deleted_note"]

    # After repayment getting unresolved, transaction came back with the settlement of 25
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.00)


@pytest.mark.asyncio
async def test_unresolve_repayment_as_irrelevant_user(
    bob_paid_john_owes, get_settlement, create_repayment, unresolve_repayment
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    dung_headers = scenario.dung_headers
    bob_headers = scenario.bob_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    repayment_data = await create_repayment(bob_headers, group_id, repayment_payload)

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # Then, Dung tried to unresolve the repayment ==> SHOULD FAIL
    unresolve_payload = {"deleted_note": ""}
    body = await unresolve_repayment(
        dung_headers,
        group_id,
        repayment_data["id"],
        unresolve_payload,
        expected_status=403,
    )

    assert "You are not allowed to unresolve this repayment!" in body["error"]

    # Current settlement unchanged, there is still 0 transaction
    settlement_data, _ = await get_settlement(dung_headers, group_id)
    assert len(settlement_data["transactions"]) == 0


@pytest.mark.asyncio
async def test_unresolve_repayment_duplicate(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
    unresolve_repayment,
    get_repayments,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    bob_headers = scenario.bob_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    repayment_data = await create_repayment(bob_headers, group_id, repayment_payload)

    # After repayment, there is no more transaction
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 0

    # Then, Bob unresolved the repayment
    unresolve_payload = {"deleted_note": "I didn't receive anything"}
    unresolve_data = await unresolve_repayment(
        bob_headers, group_id, repayment_data["id"], unresolve_payload
    )

    assert unresolve_data["is_deleted"] is True
    assert unresolve_data["deleted_at"] is not None
    assert unresolve_data["deleted_by"]["id"] == bob.id
    assert unresolve_data["deleted_note"] == unresolve_payload["deleted_note"]

    # After repayment getting unresolved, transaction came back with the settlement of 25
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.00)

    # Somehow Bob sent the second unresolve request (double click) ==> SHOULD FAIL
    unresolve_payload_duplicate = {
        "deleted_note": "I didn't receive anything duplicated"
    }
    body = await unresolve_repayment(
        bob_headers,
        group_id,
        repayment_data["id"],
        unresolve_payload_duplicate,
        expected_status=409,
    )

    assert "Repayment was already unresolved!" in body["error"]

    # Current settlement unchanged, there is still 1 transaction
    settlement_data, _ = await get_settlement(bob_headers, group_id)
    assert len(settlement_data["transactions"]) == 1

    # The original repayment row is unchanged
    repayments_data = await get_repayments(bob_headers, group_id)
    assert len(repayments_data) == 1
    assert repayments_data[0]["deleted_by"]["id"] == bob.id
    assert repayments_data[0]["deleted_note"] == unresolve_payload["deleted_note"]


@pytest.mark.asyncio
async def test_resolve_repayment_after_undoing(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
    unresolve_repayment,
    get_repayments,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    bob_headers = scenario.bob_headers
    group_id = scenario.group_id

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    repayment_data = await create_repayment(bob_headers, group_id, repayment_payload)

    # Then, Bob unresolved the repayment
    unresolve_payload = {"deleted_note": "I didn't receive anything"}
    unresolve_data = await unresolve_repayment(
        bob_headers, group_id, repayment_data["id"], unresolve_payload
    )

    assert unresolve_data["is_deleted"] is True

    # After repayment getting unresolved, transaction came back with the settlement of 25
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.00)

    # Finally, Bob resolve the repayment again
    resolve_data = await create_repayment(bob_headers, group_id, repayment_payload)

    # New entry for this repayment (different ids)
    assert resolve_data["id"] != repayment_data["id"]
    assert resolve_data["amount"] == pytest.approx(25.0)
    assert resolve_data["from_user"]["id"] == john.id
    assert resolve_data["to_user"]["id"] == bob.id
    assert resolve_data["created_by"]["id"] == bob.id  # Bob created the repayment entry
    assert resolve_data["is_deleted"] is False
    assert resolve_data["deleted_at"] is None

    # Two repayment rows
    repayments_data = await get_repayments(bob_headers, group_id)

    assert len(repayments_data) == 2
    # The first one is the latest
    assert repayments_data[0]["id"] == resolve_data["id"]
    assert repayments_data[0]["is_deleted"] is False
    # The older one is the deleted
    assert repayments_data[1]["id"] == unresolve_data["id"]
    assert repayments_data[1]["is_deleted"] is True


@pytest.mark.asyncio
async def test_get_repayments(
    bob_paid_john_owes,
    get_settlement,
    create_repayment,
    get_repayments,
):
    # Scenario: Alice is the admin, Bob paid the expense of 50 and shared with John 50/50
    scenario = bob_paid_john_owes

    bob = scenario.bob
    john = scenario.john
    alice_headers = scenario.alice_headers
    bob_headers = scenario.bob_headers
    john_headers = scenario.john_headers
    dung_headers = scenario.dung_headers
    group_id = scenario.group_id

    # Before repayment, John should owe Bob 25 (1 transaction)
    settlement_data, _ = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 1

    # Exact repayment: John paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": john.id,
        "to_user_id": bob.id,
    }
    # Repayment created by to_user (Bob)
    await create_repayment(bob_headers, group_id, repayment_payload)

    # Get repayments as group admin
    repayments_data = await get_repayments(alice_headers, group_id)
    assert len(repayments_data) == 1
    assert repayments_data[0]["from_user"]["id"] == john.id
    assert repayments_data[0]["amount"] == 25

    # Get repayments as to_user
    repayments_data = await get_repayments(bob_headers, group_id)
    assert len(repayments_data) == 1
    assert repayments_data[0]["from_user"]["id"] == john.id
    assert repayments_data[0]["amount"] == 25

    # Get repayments as from_user
    repayments_data = await get_repayments(john_headers, group_id)
    assert len(repayments_data) == 1
    assert repayments_data[0]["from_user"]["id"] == john.id
    assert repayments_data[0]["amount"] == 25

    # Get repayments as irrelevant user
    repayments_data = await get_repayments(dung_headers, group_id)
    assert len(repayments_data) == 1
    assert repayments_data[0]["from_user"]["id"] == john.id
    assert repayments_data[0]["amount"] == 25
