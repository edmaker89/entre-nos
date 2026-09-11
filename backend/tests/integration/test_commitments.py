"""BUY-01/SPLIT-01/DATA-01: purchase preview and persisted amounts."""

from uuid import uuid4
import pytest


def create_card(client):
    return client.post(
        "/api/v1/cards",
        json={
            "name": "Santander",
            "institution": "Santander",
            "holder_id": client.user_id,
            "closing_day": 25,
            "due_day": 5,
        },
        headers={"Idempotency-Key": str(uuid4())},
    ).json()["id"]


def purchase_body(client, card=None):
    return {
        "description": "Celular",
        "buyer_id": client.other_id,
        "card_id": card,
        "purchased_at": "2026-09-24",
        "total_cents": 30000,
        "count": 3,
        "shares": [{"user_id": client.other_id, "weight": 30000}],
    }


@pytest.mark.parametrize(
    "day,first,review",
    [(24, "2026-10-01", False), (25, "2026-10-01", True), (26, "2026-11-01", False)],
)
def test_preview_save(client, day, first, review):
    data = purchase_body(client, create_card(client))
    data["purchased_at"] = f"2026-09-{day}"
    preview = client.post("/api/v1/commitments/preview", json=data)
    assert preview.status_code == 200
    assert preview.json()["installments"][0]["month"] == first
    assert preview.json()["installments"][0]["needs_review"] == review
    key = str(uuid4())
    saved = client.post("/api/v1/commitments", json=data, headers={"Idempotency-Key": key})
    assert saved.status_code == 200
    body = saved.json()
    assert [p["amount_cents"] for p in body["installments"]] == [10000] * 3
    assert body["shares"][0]["user_id"] == client.other_id
    assert body["installments"][0]["month"] == first
    assert (
        client.post("/api/v1/commitments", json=data, headers={"Idempotency-Key": key}).json()["id"]
        == body["id"]
    )
    assert client.get(f"/api/v1/commitments/{body['id']}").json()["pending_count"] == 3


def test_invalid_purchase_leaves_no_records(client):
    data = purchase_body(client)
    for change in [
        {"total_cents": 0},
        {"count": 121},
        {"description": "  "},
        {"purchased_at": "invalid"},
        {"shares": [{"user_id": client.user_id, "weight": 1}]},
    ]:
        assert (
            client.post(
                "/api/v1/commitments",
                json={**data, **change},
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 422
        )
    assert client.get("/api/v1/commitments").json() == []


@pytest.mark.parametrize("weights,difference,message", [([7000, 2000], 1000, "Faltam R$ 10,00"), ([7000, 4000], -1000, "Sobram R$ 10,00")])
def test_split_difference_explained_without_saving(client, weights, difference, message):
    result = client.post("/api/v1/commitments", json={
        **purchase_body(client), "total_cents": 10000,
        "shares": [{"user_id": person, "weight": weight} for person, weight in zip([client.user_id, client.other_id], weights)]
    }, headers={"Idempotency-Key": str(uuid4())})
    assert result.status_code == 422
    assert result.json()["difference_cents"] == difference
    assert result.json()["fields"] == ["shares"]
    assert message in result.json()["message"]
    assert client.get("/api/v1/commitments").json() == []
