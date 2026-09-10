"""ADV-01: preserve original installment, forecast one obligation, reject duplicates."""

from uuid import uuid4
from test_commitments import create_card, purchase_body


def imported_car(client):
    return client.post(
        "/api/v1/commitments/import",
        json={
            "description": "Carro",
            "buyer_id": client.user_id,
            "first_month": "2026-10-01",
            "original_count": 48,
            "numbers": list(range(10, 45)),
            "installment_cents": 191900,
            "shares": [{"user_id": client.user_id, "weight": 1}],
        },
        headers={"Idempotency-Key": str(uuid4())},
    ).json()


def test_plan_car_advance(client):
    c = imported_car(client)
    last = c["installments"][-1]
    body = {
        "commitment_id": c["id"],
        "version": c["version"],
        "installment_ids": [last["id"]],
        "planned_date": "2026-10-05",
        "amount_cents": 108400,
    }
    r = client.post("/api/v1/advances/preview", json=body)
    assert r.status_code == 200
    assert r.json()["discount_cents"] == 83500
    r = client.post("/api/v1/advances", json=body, headers={"Idempotency-Key": str(uuid4())})
    assert r.status_code == 200
    assert r.json()["state"] == "planned"
    after = client.get(f"/api/v1/commitments/{c['id']}").json()
    assert after["pending_count"] == 35
    assert after["original_count"] == 48
    last = after["installments"][-1]
    assert (last["number"], last["amount_cents"], last["month"], last["original_month"]) == (
        44,
        108400,
        "2026-10-01",
        "2029-08-01",
    )
    assert (
        sum(p["amount_cents"] for p in after["installments"] if p["month"] == "2026-10-01")
        == 300300
    )
    assert (
        client.post(
            "/api/v1/advances",
            json={**body, "version": after["version"]},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )


def test_credit_card_advance_without_discount(client):
    c = client.post(
        "/api/v1/commitments",
        json=purchase_body(client, create_card(client)),
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    body = {
        "commitment_id": c["id"],
        "version": c["version"],
        "installment_ids": [p["id"] for p in c["installments"][1:]],
        "planned_date": "2026-10-01",
        "amount_cents": 20000,
    }
    r = client.post("/api/v1/advances", json=body, headers={"Idempotency-Key": str(uuid4())})
    assert r.status_code == 200
    after = client.get(f"/api/v1/commitments/{c['id']}").json()
    assert [p["month"] for p in after["installments"]] == ["2026-10-01"] * 3
    assert [p["amount_cents"] for p in after["installments"]] == [10000] * 3
    assert len({p["cycle_id"] for p in after["installments"]}) == 1


def test_advance_rejects_paid_installment_without_changing_schedule(client):
    """ADV AC08: a paid installment cannot be anticipated again."""
    c = imported_car(client)
    last = c["installments"][-1]
    paid = client.post(
        f"/api/v1/installments/{last['id']}/pay",
        json={"version": last["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert paid.status_code == 200
    before = client.get(f"/api/v1/commitments/{c['id']}").json()
    result = client.post(
        "/api/v1/advances",
        json={"commitment_id": c["id"], "version": before["version"],
              "installment_ids": [last["id"]], "planned_date": "2026-10-05",
              "amount_cents": 108400},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert result.status_code == 409
    assert result.json()["code"] == "paid"
    assert client.get(f"/api/v1/commitments/{c['id']}").json() == before
    assert client.get("/api/v1/advances").json() == []


def test_advance_rejects_amount_above_original_without_writing(client):
    """ADV AC08: charges are outside the anticipation flow."""
    c = imported_car(client)
    result = client.post(
        "/api/v1/advances",
        json={"commitment_id": c["id"], "version": c["version"],
              "installment_ids": [c["installments"][-1]["id"]],
              "planned_date": "2026-10-05", "amount_cents": 191901},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert result.status_code == 422
    assert result.json()["code"] == "invalid_amount"
    assert client.get(f"/api/v1/commitments/{c['id']}").json() == c
    assert client.get("/api/v1/advances").json() == []
