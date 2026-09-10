"""MONTH-01 AC02–07."""

from uuid import uuid4
from test_commitments import purchase_body


def test_month_totals_filters_and_empty(client):
    for user, amount in [(client.user_id, 10000), (client.other_id, 5000)]:
        c = client.post(
            "/api/v1/commitments",
            json={
                **purchase_body(client),
                "count": 1,
                "first_month": "2026-10-01",
                "total_cents": amount,
                "shares": [{"user_id": user, "weight": amount}],
            },
            headers={"Idempotency-Key": str(uuid4())},
        ).json()
        if user == client.user_id:
            part = c["installments"][0]
            assert (
                client.post(
                    f"/api/v1/installments/{part['id']}/pay",
                    json={"version": 1, "paid_at": "2026-10-05"},
                    headers={"Idempotency-Key": str(uuid4())},
                ).status_code
                == 200
            )
    r = client.get("/api/v1/months/2026-10")
    assert r.status_code == 200
    assert r.json()["totals"] == {"expected": 15000, "paid": 10000, "remaining": 5000}
    r = client.get(f"/api/v1/months/2026-10?person_id={client.other_id}")
    assert r.json()["totals"] == {"expected": 5000, "paid": 0, "remaining": 5000}
    assert len(r.json()["items"]) == 1
    assert r.json()["family_total"] == 15000
    assert client.get("/api/v1/months/2026-11").json()["totals"] == {
        "expected": 0,
        "paid": 0,
        "remaining": 0,
    }
    forecast = client.get("/api/v1/forecast?from_month=2026-10&months=12").json()
    assert len(forecast) == 12
    assert forecast[0]["totals"]["expected"] == 15000
    assert forecast[-1]["month"] == "2027-09"
