"""MONTH-01 AC08: explicit closure and invalidation."""

from uuid import uuid4
from test_commitments import purchase_body


def test_month_closure_rejects_pending_and_invalidates(client):
    assert (
        client.post(
            "/api/v1/months/2026-10/close", json={}, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 200
    )
    c = client.post(
        "/api/v1/commitments",
        json={**purchase_body(client), "first_month": "2026-10-01", "count": 1},
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    assert (
        client.post(
            "/api/v1/months/2026-10/close", json={}, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 409
    )
    assert c["installments"][0]["paid_at"] is None
    part = c["installments"][0]
    r = client.post(
        f"/api/v1/installments/{part['id']}/pay",
        json={"version": part["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert (
        client.post(
            "/api/v1/months/2026-10/close", json={}, headers={"Idempotency-Key": str(uuid4())}
        ).json()["closed"]
        is True
    )
    assert (
        client.post(
            f"/api/v1/installments/{part['id']}/reopen",
            json={"version": r.json()["version"]},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/months/2026-10/close", json={}, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 409
    )
