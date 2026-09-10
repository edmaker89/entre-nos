"""SETTLE-01 AC01/03/06: shift, version conflict and deletion."""

from uuid import uuid4
from test_commitments import purchase_body, create_card


def test_shift_and_delete(client):
    c = client.post(
        "/api/v1/commitments",
        json=purchase_body(client, create_card(client)),
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    data = {"version": 1, "first_month": "2026-11-01"}
    preview = client.post(f"/api/v1/commitments/{c['id']}/preview-shift", json=data)
    assert [p["month"] for p in preview.json()["installments"]] == [
        "2026-11-01",
        "2026-12-01",
        "2027-01-01",
    ]
    r = client.post(
        f"/api/v1/commitments/{c['id']}/shift", json=data, headers={"Idempotency-Key": str(uuid4())}
    )
    assert r.status_code == 200
    assert [p["amount_cents"] for p in r.json()["installments"]] == [10000] * 3
    assert (
        client.post(
            f"/api/v1/commitments/{c['id']}/shift",
            json=data,
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/v1/commitments/{c['id']}?version=2&confirm=false",
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"/api/v1/commitments/{c['id']}?version=2&confirm=true",
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/commitments/{c['id']}").status_code == 404
    assert client.get("/api/v1/commitments").json() == []


def test_paid_or_anticipated_purchase_cannot_shift(client):
    from datetime import date
    from app.db.unit_of_work import transaction
    from app.db.models import Installment, Advance

    c = client.post(
        "/api/v1/commitments", json=purchase_body(client), headers={"Idempotency-Key": str(uuid4())}
    ).json()
    with transaction(client.family_id) as db:
        db.get(Installment, c["installments"][0]["id"]).paid_at = date(2026, 10, 5)
    assert (
        client.post(
            f"/api/v1/commitments/{c['id']}/shift",
            json={"version": 1, "first_month": "2026-11-01"},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
    with transaction(client.family_id) as db:
        db.get(Installment, c["installments"][0]["id"]).paid_at = None
        db.add(
            Advance(
                family_id=client.family_id,
                commitment_id=c["id"],
                month=date(2026, 10, 1),
                planned_date=date(2026, 10, 5),
                amount_cents=10000,
            )
        )
    assert (
        client.post(
            f"/api/v1/commitments/{c['id']}/shift",
            json={"version": 1, "first_month": "2026-11-01"},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 409
    )
