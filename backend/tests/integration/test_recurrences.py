"""BILL-01: occurrences, estimates and end boundaries."""

from uuid import uuid4


def test_recurring_occurrences_are_unique_and_preserve_past(client):
    body = {
        "description": "Energia",
        "amount_cents": 36000,
        "variable": True,
        "due_day": 5,
        "start_month": "2026-10-01",
        "shares": [{"user_id": client.user_id, "weight": 1}],
    }
    r = client.post("/api/v1/recurrences", json=body, headers={"Idempotency-Key": str(uuid4())})
    assert r.status_code == 200
    id = r.json()["id"]
    first = client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0]
    assert [o["amount_cents"] for o in first["occurrences"]] == [36000] * 3
    assert all(o["estimated"] for o in first["occurrences"])
    assert (
        len(
            client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0][
                "occurrences"
            ]
        )
        == 3
    )
    november = first["occurrences"][1]
    r = client.patch(
        f"/api/v1/occurrences/{november['id']}",
        json={"version": 1, "amount_cents": 38000},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 200
    after = client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0]
    assert [o["amount_cents"] for o in after["occurrences"]] == [36000, 38000, 38000]
    assert after["occurrences"][1]["estimated"] is False
    assert (
        client.post(
            f"/api/v1/recurrences/{id}/end",
            json={"version": after["version"], "end_month": "2026-12-01"},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 200
    )
    assert (
        len(
            client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0][
                "occurrences"
            ]
        )
        == 2
    )


def test_older_correction_does_not_override_newer_confirmed_amount(client):
    """BILL-01: estimates use the latest known value before each month."""
    client.post(
        "/api/v1/recurrences",
        json={"description": "Energia", "amount_cents": 36000, "variable": True,
              "due_day": 5, "start_month": "2026-10-01",
              "shares": [{"user_id": client.user_id, "weight": 1}]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    rows = client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0]["occurrences"]
    for row, amount in [(rows[1], 38000), (rows[0], 37000)]:
        result = client.patch(
            f"/api/v1/occurrences/{row['id']}",
            json={"version": row["version"], "amount_cents": amount},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert result.status_code == 200
    actual = client.get("/api/v1/recurrences?from_month=2026-10-01&months=4").json()[0]["occurrences"]
    assert [o["amount_cents"] for o in actual] == [37000, 38000, 38000, 38000]
    assert [o["estimated"] for o in actual] == [False, False, True, True]
