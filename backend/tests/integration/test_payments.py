"""SETTLE-01 AC02–04 / MONTH-01 AC08."""

from uuid import uuid4
from test_commitments import purchase_body, create_card


def test_invoice_payment_and_reopening(client):
    c = client.post(
        "/api/v1/commitments",
        json={**purchase_body(client, create_card(client)), "count": 1},
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    cycle = client.get(f"/api/v1/cards/{c['card_id']}/cycles").json()[0]
    key = str(uuid4())
    body = {"version": cycle["version"], "paid_at": "2026-11-05"}
    r = client.post(
        f"/api/v1/invoices/{cycle['id']}/pay", json=body, headers={"Idempotency-Key": key}
    )
    assert r.status_code == 200
    assert (
        client.post(
            f"/api/v1/invoices/{cycle['id']}/pay", json=body, headers={"Idempotency-Key": key}
        ).status_code
        == 200
    )
    after = client.get(f"/api/v1/commitments/{c['id']}").json()
    assert len(after["installments"]) == 1
    assert after["installments"][0]["amount_cents"] == 30000
    assert after["installments"][0]["month"] == "2026-10-01"
    assert after["installments"][0]["paid_at"] == "2026-11-05"
    assert after["pending_count"] == 0
    assert (
        client.patch(
            f"/api/v1/commitments/{c['id']}",
            json={"version": after["version"], "description": "Changed"},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    r = client.post(
        f"/api/v1/invoices/{cycle['id']}/reopen",
        json={"version": r.json()["version"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 200
    assert client.get(f"/api/v1/commitments/{c['id']}").json()["pending_count"] == 1
