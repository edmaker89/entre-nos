"""EDIT-01 AC1/AC3/AC4: preview transfer of all open obligations."""

from uuid import uuid4

from test_commitments import purchase_body


def write(client, path, body):
    return client.post(
        "/api/v1" + path,
        json=body,
        headers={"Idempotency-Key": str(uuid4())},
    )


def save(client, *, total=400, count=4):
    response = write(
        client,
        "/commitments",
        {
            **purchase_body(client),
            "total_cents": total,
            "count": count,
            "first_month": "2026-10-01",
            "shares": [{"user_id": client.user_id, "weight": total}],
        },
    )
    assert response.status_code == 200
    return response.json()


def pay(client, part):
    response = write(
        client,
        f"/installments/{part['id']}/pay",
        {"version": part["version"], "paid_at": "2026-10-05"},
    )
    assert response.status_code == 200


def preview(client, commitment, shares):
    return client.post(
        f"/api/v1/commitments/{commitment['id']}/responsibility-preview",
        json={"version": commitment["version"], "shares": shares},
    )


def test_preview_transfers_100_percent_of_only_open_installments(client):
    commitment = save(client)
    pay(client, commitment["installments"][0])
    pay(client, commitment["installments"][1])
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()

    response = preview(
        client,
        current,
        [{"user_id": client.other_id, "weight": 200}],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_version"] == current["version"]
    assert body["open_total_cents"] == 200
    assert body["open_installment_count"] == 2
    assert body["months"] == ["2026-12", "2027-01"]
    assert [part["number"] for part in body["installments"]] == [3, 4]
    assert all(part["before"] == [{"user_id": client.user_id, "weight": 100}] for part in body["installments"])
    assert all(part["after"] == [{"user_id": client.other_id, "weight": 100}] for part in body["installments"])
    assert len(body["preview_hash"]) == 64
    unchanged = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    assert unchanged["installments"] == current["installments"]


def test_preview_distributes_aggregate_split_with_exact_columns(client):
    commitment = save(client, total=100, count=3)
    response = preview(
        client,
        commitment,
        [
            {"user_id": client.user_id, "weight": 67},
            {"user_id": client.other_id, "weight": 33},
        ],
    )

    assert response.status_code == 200
    after = response.json()["installments"]
    assert [sum(share["weight"] for share in part["after"]) for part in after] == [34, 33, 33]
    assert sum(share["weight"] for part in after for share in part["after"] if share["user_id"] == client.user_id) == 67
    assert sum(share["weight"] for part in after for share in part["after"] if share["user_id"] == client.other_id) == 33


def test_preview_rejects_no_open_installments_and_wrong_aggregate(client):
    commitment = save(client, total=100, count=1)
    pay(client, commitment["installments"][0])
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()

    closed = preview(client, current, [{"user_id": client.other_id, "weight": 100}])
    assert closed.status_code == 409
    assert closed.json()["code"] == "no_open_obligations"

    open_commitment = save(client, total=100, count=1)
    invalid = preview(client, open_commitment, [{"user_id": client.other_id, "weight": 99}])
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_split"
    assert invalid.json()["difference_cents"] == 1


def test_preview_lists_planned_advance_linked_to_open_installments(client):
    commitment = save(client, total=300, count=3)
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

    response = preview(
        client,
        current,
        [{"user_id": client.other_id, "weight": 280}],
    )

    assert response.status_code == 200
    assert response.json()["open_total_cents"] == 280
    assert response.json()["planned_advances"] == [
        {
            "id": advance.json()["id"],
            "month": "2026-10-01",
            "amount_cents": 180,
            "installment_ids": [part["id"] for part in selected],
        }
    ]
