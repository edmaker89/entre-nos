"""ADV-01 AC02/03/07: pay, reopen and restore schedule."""

from uuid import uuid4
from test_advances import imported_car


def test_pay_reopen_cancel_advance(client):
    car = imported_car(client)
    original = car["installments"][-1]
    body = {
        "commitment_id": car["id"],
        "version": car["version"],
        "installment_ids": [original["id"]],
        "planned_date": "2026-10-05",
        "amount_cents": 108400,
    }
    plan = client.post(
        "/api/v1/advances", json=body, headers={"Idempotency-Key": str(uuid4())}
    ).json()
    r = client.post(
        f"/api/v1/advances/{plan['id']}/pay",
        json={"version": plan["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 200
    assert r.json()["state"] == "paid"
    after = client.get(f"/api/v1/commitments/{car['id']}").json()
    assert (after["pending_count"], after["last_open_number"], after["original_count"]) == (
        34,
        43,
        48,
    )
    assert (
        client.post(
            f"/api/v1/advances/{plan['id']}/cancel",
            json={"version": r.json()["version"]},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    r = client.post(
        f"/api/v1/advances/{plan['id']}/reopen",
        json={"version": r.json()["version"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.json()["state"] == "planned"
    r = client.post(
        f"/api/v1/advances/{plan['id']}/cancel",
        json={"version": r.json()["version"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.json()["state"] == "cancelled"
    after = client.get(f"/api/v1/commitments/{car['id']}").json()
    last = after["installments"][-1]
    assert (last["month"], last["amount_cents"], last["due_date"]) == (
        original["month"],
        original["amount_cents"],
        original["due_date"],
    )
    assert after["pending_count"] == 35
