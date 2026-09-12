"""EDIT-02 AC2-AC4: full edit preview and paid-field restrictions."""

from uuid import uuid4

from test_commitments import create_card, purchase_body


def write(client, path, body):
    return client.post(
        "/api/v1" + path,
        json=body,
        headers={"Idempotency-Key": str(uuid4())},
    )


def save(client, *, card_id=None, total=200, count=2):
    response = write(
        client,
        "/commitments",
        {
            **purchase_body(client, card_id),
            "total_cents": total,
            "count": count,
            "first_month": "2026-10-01",
            "shares": [{"user_id": client.user_id, "weight": total}],
            "category": "Casa",
        },
    )
    assert response.status_code == 200
    return response.json()


def edit_body(commitment, **changes):
    body = {
        "version": commitment["version"],
        "description": commitment["description"],
        "category": commitment["category"],
        "buyer_id": commitment["buyer_id"],
        "card_id": commitment["card_id"],
        "purchased_at": commitment["purchased_at"],
        "total_cents": commitment["total_cents"],
        "count": commitment["original_count"],
        "first_month": commitment["installments"][0]["month"],
        "shares": [
            {"user_id": share["user_id"], "weight": share["weight"]}
            for share in commitment["shares"]
        ],
    }
    return {**body, **changes}


def preview(client, commitment, **changes):
    return client.post(
        f"/api/v1/commitments/{commitment['id']}/edit-preview",
        json=edit_body(commitment, **changes),
    )


def test_unpaid_preview_allows_full_contract_change_and_is_read_only(client):
    commitment = save(client)
    card_id = create_card(client)
    response = preview(
        client,
        commitment,
        description="Notebook",
        category="Trabalho",
        buyer_id=client.other_id,
        card_id=card_id,
        purchased_at="2026-11-20",
        total_cents=303,
        count=3,
        first_month="2026-12-01",
        shares=[{"user_id": client.other_id, "weight": 303}],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_version"] == commitment["version"]
    assert body["has_payments"] is False
    assert body["allowed_fields"] == [
        "description",
        "category",
        "buyer_id",
        "card_id",
        "purchased_at",
        "total_cents",
        "count",
        "first_month",
        "shares",
    ]
    assert body["after"]["commitment"]["description"] == "Notebook"
    assert body["after"]["commitment"]["buyer_id"] == client.other_id
    assert [part["amount_cents"] for part in body["after"]["installments"]] == [101, 101, 101]
    assert [part["month"] for part in body["after"]["installments"]] == [
        "2026-12-01",
        "2027-01-01",
        "2027-02-01",
    ]
    assert len(body["preview_hash"]) == 64
    unchanged = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    assert unchanged["description"] == commitment["description"]
    assert unchanged["total_cents"] == 200


def test_partially_paid_preview_allows_only_description_and_category(client):
    commitment = save(client)
    part = commitment["installments"][0]
    assert write(
        client,
        f"/installments/{part['id']}/pay",
        {"version": part["version"], "paid_at": "2026-10-05"},
    ).status_code == 200
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()

    allowed = preview(client, current, description="Mercado", category="Alimentação")
    assert allowed.status_code == 200
    assert allowed.json()["has_payments"] is True
    assert allowed.json()["allowed_fields"] == ["description", "category"]
    assert allowed.json()["after"]["commitment"]["description"] == "Mercado"
    assert allowed.json()["after"]["installments"] == allowed.json()["before"]["installments"]

    blocked = preview(client, current, total_cents=300)
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "paid_fields_locked"
    assert blocked.json()["fields"] == ["total_cents"]


def test_preview_reports_existing_cycles_and_planned_advances(client):
    card_id = create_card(client)
    commitment = save(client, card_id=card_id, total=300, count=3)
    selected = commitment["installments"][1:]
    advance = write(
        client,
        "/advances",
        {
            "commitment_id": commitment["id"],
            "version": commitment["version"],
            "installment_ids": [part["id"] for part in selected],
            "planned_date": "2026-10-01",
            "amount_cents": 180,
        },
    )
    assert advance.status_code == 200
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()

    response = preview(client, current, description="Compra ajustada")

    assert response.status_code == 200
    assert {cycle["month"] for cycle in response.json()["affected_cycles"]} == {
        "2026-10-01",
        "2026-11-01",
        "2026-12-01",
    }
    assert response.json()["planned_advances"] == [
        {
            "id": advance.json()["id"],
            "state": "planned",
            "amount_cents": 180,
            "installment_ids": [part["id"] for part in selected],
        }
    ]
