"""EDIT-01/EDIT-02: installment responsibility is an obligation snapshot."""

from uuid import uuid4

from sqlalchemy import text

from test_commitments import purchase_body


def save(client, body):
    response = client.post(
        "/api/v1/commitments",
        json=body,
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    return response.json()


def test_creation_persists_exact_snapshot_per_installment(client):
    result = save(
        client,
        {
            **purchase_body(client),
            "total_cents": 101,
            "count": 2,
            "shares": [
                {"user_id": client.user_id, "weight": 51},
                {"user_id": client.other_id, "weight": 50},
            ],
        },
    )

    assert [part["amount_cents"] for part in result["installments"]] == [51, 50]
    assert [part["shares"] for part in result["installments"]] == [
        [
            {"user_id": client.user_id, "weight": 26, "position": 0},
            {"user_id": client.other_id, "weight": 25, "position": 1},
        ],
        [
            {"user_id": client.user_id, "weight": 26, "position": 0},
            {"user_id": client.other_id, "weight": 24, "position": 1},
        ],
    ]
    assert [sum(share["weight"] for share in part["shares"]) for part in result["installments"]] == [51, 50]


def test_import_persists_snapshots_for_only_the_imported_open_obligations(client):
    response = client.post(
        "/api/v1/commitments/import",
        json={
            "description": "Financiamento",
            "buyer_id": client.user_id,
            "first_month": "2026-10-01",
            "original_count": 12,
            "numbers": [10, 11, 12],
            "installment_cents": 101,
            "shares": [
                {"user_id": client.user_id, "weight": 2},
                {"user_id": client.other_id, "weight": 1},
            ],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 200
    parts = response.json()["installments"]
    assert [part["number"] for part in parts] == [10, 11, 12]
    assert [sum(share["weight"] for share in part["shares"]) for part in parts] == [101, 101, 101]
    assert sum(
        share["weight"]
        for part in parts
        for share in part["shares"]
        if share["user_id"] == client.user_id
    ) == 204
    assert sum(
        share["weight"]
        for part in parts
        for share in part["shares"]
        if share["user_id"] == client.other_id
    ) == 99


def test_details_and_month_filter_keep_paid_snapshot_after_template_change(client, engine):
    result = save(
        client,
        {
            **purchase_body(client),
            "total_cents": 200,
            "count": 2,
            "first_month": "2026-10-01",
            "shares": [{"user_id": client.user_id, "weight": 200}],
        },
    )
    first = result["installments"][0]
    paid = client.post(
        f"/api/v1/installments/{first['id']}/pay",
        json={"version": first["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert paid.status_code == 200

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE responsibility_shares SET user_id=:other "
                "WHERE commitment_id=:commitment"
            ),
            {"other": client.other_id, "commitment": result["id"]},
        )

    details = client.get(f"/api/v1/commitments/{result['id']}").json()
    assert details["installments"][0]["shares"] == [
        {"user_id": client.user_id, "weight": 100, "position": 0}
    ]
    assert details["installments"][1]["shares"] == [
        {"user_id": client.user_id, "weight": 100, "position": 0}
    ]
    october = client.get(f"/api/v1/months/2026-10?person_id={client.user_id}").json()
    assert october["totals"] == {"expected": 100, "paid": 100, "remaining": 0}
    assert client.get(f"/api/v1/months/2026-10?person_id={client.other_id}").json()[
        "items"
    ] == []


def test_month_uses_each_installments_own_snapshot(client):
    result = save(
        client,
        {
            **purchase_body(client),
            "total_cents": 201,
            "count": 2,
            "first_month": "2026-10-01",
            "shares": [
                {"user_id": client.user_id, "weight": 101},
                {"user_id": client.other_id, "weight": 100},
            ],
        },
    )

    october = client.get("/api/v1/months/2026-10").json()
    november = client.get("/api/v1/months/2026-11").json()
    assert october["items"][0]["shares"] == [
        {"user_id": client.user_id, "name": "Douglas", "amount_cents": 51},
        {"user_id": client.other_id, "name": "Vanessa", "amount_cents": 50},
    ]
    assert november["items"][0]["shares"] == [
        {"user_id": client.user_id, "name": "Douglas", "amount_cents": 51},
        {"user_id": client.other_id, "name": "Vanessa", "amount_cents": 49},
    ]
    assert result["shares"][0]["weight"] == 101
