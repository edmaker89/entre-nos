"""MIG-01 AC01–03 / BILL-01 AC03."""

from uuid import uuid4


def test_import_remaining_installments(client):
    data = {
        "description": "Panelas",
        "buyer_id": client.other_id,
        "first_month": "2026-10-01",
        "original_count": 12,
        "numbers": [10, 11, 12],
        "installment_cents": 4351,
        "shares": [{"user_id": client.other_id, "weight": 1}],
    }
    r = client.post(
        "/api/v1/commitments/import", json=data, headers={"Idempotency-Key": str(uuid4())}
    )
    assert r.status_code == 200
    assert [p["number"] for p in r.json()["installments"]] == [10, 11, 12]
    assert [p["month"] for p in r.json()["installments"]] == [
        "2026-10-01",
        "2026-11-01",
        "2026-12-01",
    ]
    assert sum(p["amount_cents"] for p in r.json()["installments"]) == 13053
    car = {
        **data,
        "original_count": 48,
        "numbers": list(range(10, 45)),
        "installment_cents": 191900,
    }
    r = client.post(
        "/api/v1/commitments/import", json=car, headers={"Idempotency-Key": str(uuid4())}
    )
    assert r.json()["pending_count"] == 35
    assert r.json()["original_count"] == 48
    assert r.json()["last_open_number"] == 44
    for numbers in [[0], [49], [10, 10], []]:
        assert (
            client.post(
                "/api/v1/commitments/import",
                json={**car, "numbers": numbers},
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 422
        )
