import pytest


@pytest.mark.asyncio
async def test_create_repayment_as_group_admin(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with John

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": john.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, John should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[john.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

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

    # After repayment, Johhn sent Bob 25, everyone's balance should be 0
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 0
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[bob.id]["received"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["sent"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(0.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_create_repayment_as_to_user(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)
    bob_headers = headers_for(bob)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with John

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": bob.id, "ratio": 1 / 2},
                {"user_id": john.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, John should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[john.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

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

    # After repayment, John sent Bob 25, everyone's balance should be 0
    settlement_data, settlement_balances = await get_settlement(bob_headers, group_id)

    assert len(settlement_data["transactions"]) == 0
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[bob.id]["received"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["sent"] == pytest.approx(25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(0.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_create_repayment_as_from_user(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)
    john_headers = headers_for(john)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with John

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": bob.id, "ratio": 1 / 2},
                {"user_id": john.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, John should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[john.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

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

    # After repayment, John sent Bob 25, everyone's balance should be 0
    settlement_data, settlement_balances = await get_settlement(john_headers, group_id)

    assert len(settlement_data["transactions"]) == 0
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[bob.id]["received"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["sent"] == pytest.approx(25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(0.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)


# Another group member (not admin) creates repayment that they are not either from_user or to_user
@pytest.mark.asyncio
async def test_create_repayment_as_irrelevant_group_member(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)
    john_headers = headers_for(john)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with Alice

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": bob.id, "ratio": 1 / 2},
                {"user_id": alice.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, Alice should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert alice.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[alice.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[alice.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

    # Exact repayment: Alice paid Bob 25
    repayment_payload = {
        "amount": 25,
        "from_user_id": alice.id,
        "to_user_id": bob.id,
    }

    # Repayment created by a group member (John) who wasn't invovled in the transaction
    # Expect this call to FAIL
    body = await create_repayment(
        john_headers, group_id, repayment_payload, expected_status=403
    )

    assert "You are not allowed to create repayment" in body["error"]

    # Current settlement is still the same
    settlement_data, _ = await get_settlement(alice_headers, group_id)
    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.0)


@pytest.mark.asyncio
async def test_create_repayment_with_stale_amount(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)
    john_headers = headers_for(john)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with John

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": john.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, John should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[john.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

    # John paid Bob 30 (different from his share of 25)
    # The scenario: someone changed the total from 60 to 50 while John didn't refresh his screen and proceeded his repayment
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

    # Current settlement is still the same
    settlement_data, _ = await get_settlement(alice_headers, group_id)
    assert len(settlement_data["transactions"]) == 1
    assert settlement_data["transactions"][0]["amount"] == pytest.approx(25.0)


@pytest.mark.asyncio
async def test_create_repayment_duplicate(
    headers_for,
    create_user,
    set_up_group_with_members_and_expenses,
    get_settlement,
    create_repayment,
):
    alice = await create_user(username="alice", email="alice@example.com")
    bob = await create_user(username="bob", email="bob@example.com")
    john = await create_user(username="john", email="john@example.com")

    alice_headers = headers_for(alice)

    # Alice created the group with Bob and John as members
    # Bob paid the expense of 50, share is 50/50 with John

    members = [{"id": bob.id, "role": "member"}, {"id": john.id, "role": "member"}]
    expenses = [
        {
            "name": "Grocery",
            "value": 50,
            "payee_id": bob.id,
            "shares": [
                {"user_id": john.id, "ratio": 1 / 2},
                {"user_id": bob.id, "ratio": 1 / 2},
            ],
        }
    ]
    group_id = await set_up_group_with_members_and_expenses(
        alice_headers, group_name="Trip", members=members, expenses=expenses
    )

    # Before repayment, John should owe Bob 25
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 1
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[john.id]["received"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["sent"] == pytest.approx(0.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(-25.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(25.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

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

    # After repayment, Johhn sent Bob 25, everyone's balance should be 0
    settlement_data, settlement_balances = await get_settlement(alice_headers, group_id)

    assert len(settlement_data["transactions"]) == 0
    assert john.id in settlement_balances
    assert bob.id in settlement_balances
    assert settlement_balances[bob.id]["received"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["sent"] == pytest.approx(25.0)
    assert settlement_balances[john.id]["balance"] == pytest.approx(0.0)
    assert settlement_balances[bob.id]["balance"] == pytest.approx(0.0)
    assert settlement_data["imbalance"] == pytest.approx(0.0)

    # Somehow Alice create the repayment again (double click), expect this time to FAIL
    body = await create_repayment(
        alice_headers, group_id, repayment_payload, expected_status=409
    )

    assert "Settlement has changed, please refresh!" in body["error"]

    # Current settlement is still the same
    settlement_data, _ = await get_settlement(alice_headers, group_id)
    assert len(settlement_data["transactions"]) == 0
