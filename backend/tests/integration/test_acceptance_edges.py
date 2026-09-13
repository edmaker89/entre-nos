"""Spec acceptance gaps from independent verification, exercised over HTTP/PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select, text
from sqlalchemy.orm import Session

from app.cli import provision
from app.db.models import Commitment, Installment, Share
from app.db.unit_of_work import transaction
from app.main import app
from test_commitments import create_card, purchase_body
from test_advances import imported_car


def write(client, path, body=None, method="post"):
    return getattr(client, method)(
        "/api/v1" + path, json=body, headers={"Idempotency-Key": str(uuid4())}
    )


def get(client, path):
    return client.get("/api/v1" + path).json()


def buy(client, card=None, **changes):
    response = write(client, "/commitments", {**purchase_body(client, card), **changes})
    assert response.status_code == 200
    return response.json()


def advance_body(c, amount=108400):
    return {
        "commitment_id": c["id"],
        "version": c["version"],
        "installment_ids": [c["installments"][-1]["id"]],
        "planned_date": "2026-10-05",
        "amount_cents": amount,
    }


def session_for(family=None):
    email = f"{uuid4()}@test.local"
    provision("Family", "Member", email, "testing-password", family)
    session = TestClient(app, client=(str(uuid4()), 123))
    response = session.post(
        "/api/v1/auth/login", json={"email": email, "password": "testing-password"}
    )
    session.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return session, email


def test_family_sharing_isolation_and_relogin(client):
    """FAM AC01–03: shared household, forbidden outsiders, persistence after login."""
    c = buy(client, description="Household private purchase")
    with (
        session_for(client.family_id)[0] as member,
        session_for()[0] as outsider,
        TestClient(app) as anonymous,
    ):
        assert get(member, f"/commitments/{c['id']}") == c
        for session in [outsider, anonymous]:
            for response in [
                session.get(f"/api/v1/commitments/{c['id']}"),
                write(
                    session,
                    f"/commitments/{c['id']}",
                    {"version": 1, "description": "Stolen"},
                    "patch",
                ),
            ]:
                assert response.status_code in (401, 404)
                assert "Household private purchase" not in response.text
        assert get(client, f"/commitments/{c['id']}") == c
    session, email = session_for(client.family_id)
    with session:
        assert write(session, "/auth/logout").status_code == 200
        assert session.get(f"/api/v1/commitments/{c['id']}").status_code == 401
        assert (
            session.post(
                "/api/v1/auth/login", json={"email": email, "password": "testing-password"}
            ).status_code
            == 200
        )
        assert get(session, f"/commitments/{c['id']}") == c


@pytest.mark.parametrize(
    "day,months",
    [
        (24, ["2026-10-01", "2026-11-01", "2026-12-01"]),
        (26, ["2026-11-01", "2026-12-01", "2027-01-01"]),
    ],
)
def test_complete_purchase_schedule_and_holder_responsibility(client, day, months):
    """BUY AC01/02, SPLIT AC01/04: full schedule and independent card holder."""
    card = create_card(client)
    c = buy(client, card, purchased_at=f"2026-09-{day}")
    assert [p["month"] for p in c["installments"]] == months
    assert [p["amount_cents"] for p in c["installments"]] == [10000] * 3
    assert get(client, "/cards")[0]["holder_id"] == client.user_id
    month = get(client, "/months/" + months[0][:7])
    assert {p["id"]: p["amount_cents"] for p in month["people"]} == {
        client.user_id: 0,
        client.other_id: 10000,
    }
    assert month["totals"]["expected"] == 10000


def test_custom_split_applies_proportions_to_each_installment(client):
    """SPLIT AC04: 70/30 proportion applied independently to each installment."""
    c = buy(
        client,
        total_cents=10000,
        count=3,
        first_month="2026-10-01",
        shares=[
            {"user_id": client.user_id, "weight": 7000},
            {"user_id": client.other_id, "weight": 3000},
        ],
    )
    assert [p["amount_cents"] for p in c["installments"]] == [3334, 3333, 3333]
    for month, expected in [
        ("2026-10", [2334, 1000]),
        ("2026-11", [2334, 999]),
        ("2026-12", [2334, 999]),
    ]:
        item = get(client, "/months/" + month)["items"][0]
        assert [s["amount_cents"] for s in item["shares"]] == expected


def test_purchase_mid_write_failure_rolls_back_all_entities(client, engine):
    """BUY AC06/DATA AC05: fail after purchase/share creation, before installments finish."""

    def fail(session, *_):
        if any(isinstance(row, Installment) for row in session.new):
            session.execute(text("SELECT 'private-description-30000'::integer"))

    event.listen(Session, "before_flush", fail)
    try:
        result = write(client, "/commitments", purchase_body(client))
    finally:
        event.remove(Session, "before_flush", fail)
    assert result.status_code == 503
    with transaction(client.family_id, engine) as db:
        assert db.scalars(select(Commitment)).all() == []
        assert db.scalars(select(Share)).all() == []
        assert db.scalars(select(Installment)).all() == []


def test_fixed_rent_and_paid_recurrence_end_boundary(client):
    """BILL AC01/04: fixed rent unique and end cannot erase paid occurrence."""
    r = write(
        client,
        "/recurrences",
        {
            "description": "Aluguel",
            "amount_cents": 160000,
            "variable": False,
            "due_day": 5,
            "start_month": "2026-10-01",
            "shares": [{"user_id": client.user_id, "weight": 1}],
        },
    ).json()
    for _ in range(2):
        rows = get(client, "/recurrences?from_month=2026-10-01&months=3")[0]["occurrences"]
        assert [o["amount_cents"] for o in rows] == [160000] * 3
        assert [o["estimated"] for o in rows] == [False] * 3
    december = rows[-1]
    assert (
        write(
            client,
            f"/occurrences/{december['id']}/pay",
            {"version": december["version"], "paid_at": "2026-12-05"},
        ).status_code
        == 200
    )
    response = write(
        client, f"/recurrences/{r['id']}/end", {"version": r["version"], "end_month": "2026-12-01"}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "paid"
    actual = get(client, "/recurrences?from_month=2026-10-01&months=3")[0]["occurrences"]
    assert [o["month"] for o in actual] == ["2026-10-01", "2026-11-01", "2026-12-01"]
    assert actual[-1]["paid_at"] == "2026-12-05"


def test_import_finite_and_gaps_without_inventing_history(client):
    """BILL AC03/MIG AC02/03: exact finite schedule, exceptions, no invented past."""
    body = {
        "description": "Finito",
        "buyer_id": client.user_id,
        "first_month": "2026-10-01",
        "original_count": 4,
        "numbers": [2, 3, 4],
        "installment_cents": 20000,
        "shares": [{"user_id": client.user_id, "weight": 1}],
    }
    c = write(client, "/commitments/import", body).json()
    assert [(p["number"], p["month"], p["amount_cents"]) for p in c["installments"]] == [
        (2, "2026-10-01", 20000),
        (3, "2026-11-01", 20000),
        (4, "2026-12-01", 20000),
    ]
    gap = write(
        client, "/commitments/import", {**body, "original_count": 48, "numbers": [10, 12, 44]}
    ).json()
    assert [(p["number"], p["month"], p["paid_at"]) for p in gap["installments"]] == [
        (10, "2026-10-01", None),
        (12, "2026-12-01", None),
        (44, "2029-08-01", None),
    ]
    assert (gap["original_count"], gap["pending_count"], gap["imported"]) == (48, 3, True)
    for numbers in [[0], [49]]:
        assert write(client, "/commitments/import", {**body, "numbers": numbers}).status_code == 422
    assert len(get(client, "/commitments")) == 2


def test_shift_preserves_shares_and_delete_removes_month_totals(client, engine):
    """SETTLE AC01/06: whole schedule/shares survive shift; logical deletion clears totals."""
    c = buy(client, first_month="2026-10-01")
    shifted = write(
        client,
        f"/commitments/{c['id']}/shift",
        {"version": c["version"], "first_month": "2026-11-01"},
    ).json()
    assert [p["month"] for p in shifted["installments"]] == [
        "2026-11-01",
        "2026-12-01",
        "2027-01-01",
    ]
    assert [p["amount_cents"] for p in shifted["installments"]] == [10000] * 3
    assert shifted["shares"] == c["shares"]
    result = client.delete(
        f"/api/v1/commitments/{c['id']}?version={shifted['version']}&confirm=true",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert result.status_code == 200
    assert get(client, "/months/2026-11")["totals"]["expected"] == 0
    with transaction(client.family_id, engine) as db:
        assert db.get(Commitment, c["id"]).deleted_at is not None
        assert all(p.deleted_at is not None for p in db.scalars(select(Installment)))


@pytest.mark.parametrize("op", ["advance", "pay"])
def test_competing_advance_and_payment_only_one_wins(client, op):
    """ADV AC09: concurrent sessions cannot overwrite the first financial change."""
    c = imported_car(client)
    with session_for(client.family_id)[0] as other:

        def first():
            return write(client, "/advances", advance_body(c))

        def second():
            if op == "advance":
                return write(other, "/advances", advance_body(c))
            last = c["installments"][-1]
            return write(
                other,
                f"/installments/{last['id']}/pay",
                {"version": last["version"], "paid_at": "2026-10-05"},
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(first), pool.submit(second)]
            responses = [f.result() for f in futures]
    assert sorted(r.status_code for r in responses) == [200, 409]
    after = get(client, f"/commitments/{c['id']}")
    plans = get(client, "/advances")
    assert len(plans) == (1 if responses[0].status_code == 200 or op == "advance" else 0)
    assert after["pending_count"] == (35 if plans else 34)
    assert [p["number"] for p in after["installments"]] == list(range(10, 45))
    assert after["installments"][0]["amount_cents"] == 191900


@pytest.mark.parametrize("guard", ["manual", "confirmed", "paid", "advance"])
def test_effective_cycle_preserves_protected_purchase(client, guard):
    """CARD AC04/ADV AC10: closing changes never shift protected installments."""
    card = create_card(client)
    c = buy(
        client,
        card,
        purchased_at="2026-09-25",
        **({"first_month": "2026-10-01"} if guard == "manual" else {}),
    )
    cycles = get(client, f"/cards/{card}/cycles")
    if guard == "confirmed":
        assert (
            write(
                client, f"/cycles/{cycles[0]['id']}/confirm", {"version": cycles[0]["version"]}
            ).status_code
            == 200
        )
    if guard == "paid":
        assert (
            write(
                client,
                f"/invoices/{cycles[-1]['id']}/pay",
                {"version": cycles[-1]["version"], "paid_at": "2026-10-01"},
            ).status_code
            == 200
        )
    if guard == "advance":
        assert write(client, "/advances", advance_body(c, 10000)).status_code == 200
    before = get(client, f"/commitments/{c['id']}")
    cycle = get(client, f"/cards/{card}/cycles")[0]
    body = {"version": cycle["version"], "closing_date": "2026-09-24"}
    assert write(client, f"/cycles/{cycle['id']}/preview-close", body).json()["changes"] == []
    assert write(client, f"/cycles/{cycle['id']}/close", body, "patch").status_code == 200
    assert get(client, f"/commitments/{c['id']}") == before


def test_cycle_invalid_order_and_confirmation_flags(client):
    """CARD AC04/SETTLE AC05: invalid boundaries rejected; new purchase reopens review."""
    card = create_card(client)
    c = buy(client, card, purchased_at="2026-09-25")
    cycle = get(client, f"/cards/{card}/cycles")[0]
    for closing in ["2026-10-05", "2026-11-25"]:
        assert (
            write(
                client,
                f"/cycles/{cycle['id']}/close",
                {"version": cycle["version"], "closing_date": closing},
                "patch",
            ).status_code
            == 409
        )
    assert (
        write(client, f"/cycles/{cycle['id']}/confirm", {"version": cycle["version"]}).status_code
        == 200
    )
    assert get(client, f"/commitments/{c['id']}")["installments"][0]["needs_review"] is False
    buy(client, card, purchased_at="2026-09-25")
    assert get(client, f"/cards/{card}/cycles")[0]["confirmed"] is False
    november = get(client, f"/cards/{card}/cycles")[1]
    assert (
        write(
            client,
            f"/cycles/{november['id']}/close",
            {"version": november["version"], "closing_date": "2026-09-25"},
            "patch",
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "amount,parts", [(20000, [10000, 10000]), (19998, [9999, 9999]), (19999, [10000, 9999])]
)
def test_card_advance_amounts_shares_payment_and_reopen(client, amount, parts):
    """ADV AC05/06 and SETTLE AC03: destination only, inherited shares, invoice lifecycle."""
    card = create_card(client)
    c = buy(
        client,
        card,
        shares=[
            {"user_id": client.user_id, "weight": 15000},
            {"user_id": client.other_id, "weight": 15000},
        ],
    )
    body = {**advance_body(c, amount), "installment_ids": [p["id"] for p in c["installments"][1:]]}
    plan = write(client, "/advances", body).json()
    after = get(client, f"/commitments/{c['id']}")
    assert [p["amount_cents"] for p in after["installments"]] == [10000] + parts
    assert [p["month"] for p in after["installments"]] == ["2026-10-01"] * 3
    assert get(client, "/months/2026-11")["totals"]["expected"] == 0
    assert get(client, "/months/2026-12")["totals"]["expected"] == 0
    monthly = get(client, "/months/2026-10")
    assert monthly["totals"]["expected"] == 10000 + amount
    expected = [[5000, 5000]] + (
        [[5000, 5000], [5000, 5000]]
        if amount == 20000
        else [[5000, 4999], [5000, 4999]]
        if amount == 19998
        else [[5000, 5000], [5000, 4999]]
    )
    by_number = {i["number"]: [s["amount_cents"] for s in i["shares"]] for i in monthly["items"]}
    assert [by_number[n] for n in [1, 2, 3]] == expected
    cycle = get(client, f"/cards/{card}/cycles")[0]
    paid = write(
        client,
        f"/invoices/{cycle['id']}/pay",
        {"version": cycle["version"], "paid_at": "2026-10-05"},
    ).json()
    assert get(client, "/months/2026-10")["totals"] == {
        "expected": 10000 + amount,
        "paid": 10000 + amount,
        "remaining": 0,
    }
    current = get(client, f"/commitments/{c['id']}")
    assert current["pending_count"] == 0
    description_edit = write(
        client,
        f"/commitments/{c['id']}",
        {"version": current["version"], "description": "Changed"},
        "patch",
    )
    assert description_edit.status_code == 200
    assert description_edit.json()["description"] == "Changed"
    assert all(part["paid_at"] == "2026-10-05" for part in description_edit.json()["installments"])
    current = get(client, f"/commitments/{c['id']}")
    for payload in [
        {"description": "Changed", "total_cents": 1},
        {"description": "Changed", "shares": []},
    ]:
        assert write(
            client,
            f"/commitments/{c['id']}",
            {"version": current["version"], **payload},
            "patch",
        ).status_code == 422
    assert (
        client.delete(
            f"/api/v1/commitments/{c['id']}?version={current['version']}&confirm=true",
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    plan = get(client, "/advances")[0]
    assert plan["state"] == "paid"
    assert (
        write(client, f"/advances/{plan['id']}/cancel", {"version": plan["version"]}).json()["code"]
        == "paid"
    )
    assert (
        write(client, f"/invoices/{cycle['id']}/reopen", {"version": paid["version"]}).status_code
        == 200
    )
    assert get(client, "/advances")[0]["state"] == "planned"
    assert all(p["paid_at"] is None for p in get(client, f"/commitments/{c['id']}")["installments"])


def test_advance_destination_and_original_paid_cycle_guards(client):
    """ADV AC05/07/08: invalid destination/date, original paid invoice prevents restore."""
    card = create_card(client)
    c = buy(client, card)
    body = advance_body(c, 10000)
    for change in [
        {"planned_date": "2026-12-05"},
        {"planned_date": "2027-01-01"},
        {"amount_cents": 0},
        {"installment_ids": [p["id"] for p in c["installments"][1:]], "amount_cents": 1},
    ]:
        assert write(client, "/advances", {**body, **change}).status_code == 422
    cycle = get(client, f"/cards/{card}/cycles")[0]
    paid = write(
        client,
        f"/invoices/{cycle['id']}/pay",
        {"version": cycle["version"], "paid_at": "2026-10-05"},
    ).json()
    current = get(client, f"/commitments/{c['id']}")
    assert write(client, "/advances", advance_body(current, 10000)).json()["code"] == "paid_cycle"
    write(client, f"/invoices/{cycle['id']}/reopen", {"version": paid["version"]})
    current = get(client, f"/commitments/{c['id']}")
    plan = write(client, "/advances", advance_body(current, 10000)).json()
    original = get(client, f"/cards/{card}/cycles")[-1]
    paid = write(
        client,
        f"/invoices/{original['id']}/pay",
        {"version": original["version"], "paid_at": "2026-10-05"},
    ).json()
    assert (
        write(client, f"/advances/{plan['id']}/cancel", {"version": plan["version"]}).json()["code"]
        == "paid_cycle"
    )
    write(client, f"/invoices/{original['id']}/reopen", {"version": paid["version"]})
    assert (
        write(client, f"/advances/{plan['id']}/cancel", {"version": plan["version"]}).status_code
        == 200
    )
    restored = get(client, f"/commitments/{c['id']}")["installments"][-1]
    assert (restored["cycle_id"], restored["month"], restored["amount_cents"]) == (
        original["id"],
        "2026-12-01",
        10000,
    )


def test_car_month_lines_and_original_schedule_after_payment(client):
    """ADV AC01/03/04 and MONTH AC08: two linked lines and explicit unpaid plan."""
    c = imported_car(client)
    plan = write(client, "/advances", advance_body(c)).json()
    month = get(client, "/months/2026-10")
    assert month["totals"]["expected"] == 300300
    assert len(month["items"]) == 2
    assert {i["commitment_id"] for i in month["items"]} == {c["id"]}
    assert sorted(
        (i["number"], i["original_count"], i["amount_cents"]) for i in month["items"]
    ) == [(10, 48, 191900), (44, 48, 108400)]
    assert get(client, "/months/2029-08")["totals"]["expected"] == 0
    regular = c["installments"][0]
    write(
        client,
        f"/installments/{regular['id']}/pay",
        {"version": regular["version"], "paid_at": "2026-10-05"},
    )
    assert write(client, "/months/2026-10/close", {}).status_code == 409
    assert get(client, "/advances")[0]["state"] == "planned"
    write(
        client, f"/advances/{plan['id']}/pay", {"version": plan["version"], "paid_at": "2026-10-05"}
    )
    after = get(client, f"/commitments/{c['id']}")
    assert [p["number"] for p in after["installments"]] == list(range(10, 45))
    assert (after["installments"][0]["number"], after["installments"][0]["amount_cents"]) == (
        10,
        191900,
    )
    assert (after["last_open_number"], after["original_count"]) == (43, 48)


def test_month_default_reacts_to_explicit_closure_and_new_expense(client, monkeypatch):
    """MONTH AC08: before day ten, closure advances default; new debt invalidates it."""
    from datetime import datetime, timezone

    monkeypatch.setattr(
        "app.api.months.now", lambda: datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
    )
    assert get(client, "/months/default")["month"] == "2026-10"
    assert write(client, "/months/2026-10/close", {}).status_code == 200
    assert get(client, "/months/default")["month"] == "2026-11"
    buy(client, first_month="2026-10-01")
    assert get(client, "/months/default")["month"] == "2026-10"


@pytest.mark.parametrize(
    "change,field",
    [
        ({"description": "x" * 201}, "description"),
        ({"total_cents": -1}, "total_cents"),
        ({"count": 121}, "count"),
        ({"purchased_at": "invalid"}, "purchased_at"),
    ],
)
def test_invalid_fields_have_identifiers_and_no_persistence(client, change, field):
    """DATA AC01: validation explains affected fields without partial writes."""
    result = write(client, "/commitments", {**purchase_body(client), **change})
    assert result.status_code == 422
    assert any(field in value for value in result.json()["fields"])
    assert get(client, "/commitments") == []


def test_trimmed_description_and_minimum_cent_per_installment(client):
    """DATA AC01: trimmed boundary description and total at least installment count."""
    c = buy(client, description="  " + "x" * 200 + "  ")
    assert c["description"] == "x" * 200
    result = write(
        client,
        "/commitments",
        {
            **purchase_body(client),
            "total_cents": 2,
            "count": 3,
            "shares": [{"user_id": client.user_id, "weight": 2}],
        },
    )
    assert result.status_code == 422
    assert result.json()["fields"] == ["total_cents"]
    assert len(get(client, "/commitments")) == 1
