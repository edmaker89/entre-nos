"""CARD-01 and FAM-01 AC02."""

from uuid import uuid4

import pytest


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


def test_catalog_endpoint_exposes_all_approved_options_and_networks(client):
    response = client.get("/api/v1/cards/catalog")
    assert response.status_code == 200
    assert [item["key"] for item in response.json()["institutions"]] == [
        "nubank", "itau", "bradesco", "santander", "bb", "caixa", "inter", "c6",
        "btg", "xp", "picpay", "mercado_pago", "neon", "sicoob", "sicredi", "other",
    ]
    assert [item["key"] for item in response.json()["networks"]] == [
        "visa", "mastercard", "elo", "amex", "hipercard", "other",
    ]


def test_catalogued_card_persists_stable_key_network_and_last_four(client):
    response = client.post(
        "/api/v1/cards",
        json={"name": "Dia a dia", "institution_key": "neon", "network": "Visa",
              "last_four": "0042", "holder_id": client.user_id, "closing_day": 25,
              "due_day": 5},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.json()["institution_key"] == "neon"
    assert response.json()["institution"] == "Neon"
    assert response.json()["network"] == "visa"
    assert response.json()["last_four"] == "0042"


def test_custom_institution_uses_other_key_and_preserves_its_name(client):
    response = client.post(
        "/api/v1/cards",
        json={"name": "Cooperativa", "institution_key": "other",
              "institution": "Cooperativa Local", "holder_id": client.user_id,
              "closing_day": 12, "due_day": 20},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.json()["institution_key"] == "other"
    assert response.json()["institution"] == "Cooperativa Local"


def test_legacy_institution_only_payload_is_normalized_compatibly(client):
    response = client.post(
        "/api/v1/cards",
        json={"name": "Legado", "institution": "Banco do Brasil",
              "holder_id": client.user_id, "closing_day": 8, "due_day": 15},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.json()["institution_key"] == "bb"
    assert response.json()["institution"] == "Banco do Brasil"


@pytest.mark.parametrize("payload", [{"pan": "4111111111111111"}, {"cvv": "123"},
                                      {"card_number": "4111111111111111"}])
def test_sensitive_card_fields_are_rejected_with_specific_safe_error(client, payload):
    response = client.post(
        "/api/v1/cards",
        json={"name": "Não salvar", "institution_key": "neon", "holder_id": client.user_id,
              "closing_day": 8, "due_day": 15, **payload},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "unsupported_card_data"
    assert "quatro dígitos" in response.json()["message"]
    assert client.get("/api/v1/cards").json() == []


@pytest.mark.parametrize("last_four", ["123", "12345", "12x4"])
def test_last_four_accepts_exactly_four_digits(client, last_four):
    response = client.post(
        "/api/v1/cards",
        json={"name": "Inválido", "institution_key": "neon", "last_four": last_four,
              "holder_id": client.user_id, "closing_day": 8, "due_day": 15},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 422
    assert "body.last_four" in response.json()["fields"]
