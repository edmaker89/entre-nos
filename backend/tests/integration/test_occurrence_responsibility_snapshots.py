"""EDIT-01: recurring responsibility is snapshotted when materialized."""

from uuid import uuid4

from sqlalchemy import text


def create_rule(client, *, amount=101, shares=None):
    response = client.post(
        "/api/v1/recurrences",
        json={
            "description": "Internet",
            "amount_cents": amount,
            "variable": False,
            "due_day": 10,
            "start_month": "2026-10-01",
            "shares": shares
            or [
                {"user_id": client.user_id, "weight": 51},
                {"user_id": client.other_id, "weight": 50},
            ],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    return response.json()


def test_existing_occurrence_keeps_snapshot_and_future_uses_new_template(client, engine):
    rule = create_rule(client)
    october = client.get("/api/v1/months/2026-10").json()
    assert october["items"][0]["shares"] == [
        {"user_id": client.user_id, "name": "Douglas", "amount_cents": 51},
        {"user_id": client.other_id, "name": "Vanessa", "amount_cents": 50},
    ]

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE recurring_rules SET shares=:shares WHERE id=:id"),
            {
                "id": rule["id"],
                "shares": '[{"user_id":"%s","weight":1}]' % client.other_id,
            },
        )

    repeated = client.get("/api/v1/months/2026-10").json()
    november = client.get("/api/v1/months/2026-11").json()
    assert repeated["items"][0]["shares"] == october["items"][0]["shares"]
    assert november["items"][0]["shares"] == [
        {"user_id": client.other_id, "name": "Vanessa", "amount_cents": 101}
    ]
    assert client.get(f"/api/v1/months/2026-11?person_id={client.user_id}").json()[
        "items"
    ] == []


def test_paid_occurrence_snapshot_is_immutable_after_template_change(client, engine):
    rule = create_rule(client, amount=200, shares=[{"user_id": client.user_id, "weight": 1}])
    occurrence = client.get(
        "/api/v1/recurrences?from_month=2026-10-01&months=1"
    ).json()[0]["occurrences"][0]
    paid = client.post(
        f"/api/v1/occurrences/{occurrence['id']}/pay",
        json={"version": occurrence["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert paid.status_code == 200

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE recurring_rules SET shares=:shares WHERE id=:id"),
            {
                "id": rule["id"],
                "shares": '[{"user_id":"%s","weight":1}]' % client.other_id,
            },
        )

    douglas = client.get(f"/api/v1/months/2026-10?person_id={client.user_id}").json()
    vanessa = client.get(f"/api/v1/months/2026-10?person_id={client.other_id}").json()
    assert douglas["totals"] == {"expected": 200, "paid": 200, "remaining": 0}
    assert douglas["items"][0]["paid_at"] == "2026-10-05"
    assert vanessa["items"] == []
