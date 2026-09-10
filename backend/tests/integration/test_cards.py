"""CARD-01 and FAM-01 AC02."""

from uuid import uuid4


def test_card_create_list_and_edit(client):
    data = {
        "name": "Santander",
        "institution": "Santander",
        "holder_id": client.user_id,
        "closing_day": 25,
        "due_day": 5,
    }
    key = str(uuid4())
    r = client.post("/api/v1/cards", json=data, headers={"Idempotency-Key": key})
    assert r.status_code == 200
    card = r.json()
    assert (card["closing_day"], card["due_day"], card["holder_id"]) == (25, 5, client.user_id)
    assert (
        client.post("/api/v1/cards", json=data, headers={"Idempotency-Key": key}).json()["id"]
        == card["id"]
    )
    assert len(client.get("/api/v1/cards").json()) == 1
    r = client.patch(
        f"/api/v1/cards/{card['id']}",
        json={**data, "version": 1, "closing_day": 26},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.json()["closing_day"] == 26
    assert r.json()["version"] == 2
    r = client.post(
        "/api/v1/cards", json={**data, "closing_day": 32}, headers={"Idempotency-Key": str(uuid4())}
    )
    assert r.status_code == 422
    r = client.post(
        "/api/v1/cards",
        json={**data, "holder_id": str(uuid4())},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 422
    assert (
        client.patch(
            f"/api/v1/cards/{uuid4()}",
            json={**data, "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 404
    )
