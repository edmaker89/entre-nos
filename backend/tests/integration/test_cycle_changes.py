"""CARD-01 AC04; SETTLE-01 AC05."""

from uuid import uuid4
from test_commitments import purchase_body, create_card


def test_change_effective_closing_and_confirm(client):
    card = create_card(client)
    data = {**purchase_body(client, card), "purchased_at": "2026-09-25"}
    c = client.post(
        "/api/v1/commitments", json=data, headers={"Idempotency-Key": str(uuid4())}
    ).json()
    cycles = client.get(f"/api/v1/cards/{card}/cycles").json()
    october = next(x for x in cycles if x["month"] == "2026-10-01")
    body = {"version": october["version"], "closing_date": "2026-09-24"}
    p = client.post(f"/api/v1/cycles/{october['id']}/preview-close", json=body)
    assert p.status_code == 200
    assert p.json()["changes"][0]["first_month"] == "2026-11-01"
    r = client.patch(
        f"/api/v1/cycles/{october['id']}/close",
        json=body,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 200
    assert (
        client.get(f"/api/v1/commitments/{c['id']}").json()["installments"][0]["month"]
        == "2026-11-01"
    )
    cycle = client.get(f"/api/v1/cards/{card}/cycles").json()[1]
    r = client.post(
        f"/api/v1/cycles/{cycle['id']}/confirm",
        json={"version": cycle["version"]},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.json()["confirmed"] is True
    p = client.patch(
        f"/api/v1/cycles/{october['id']}/close",
        json={"version": r.json()["version"], "closing_date": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert p.status_code == 409
