"""EDIT-01 AC2/AC5-AC7: atomic transfer of open responsibility."""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.api import commitment_changes
from test_commitments import purchase_body


def write(client, path, body, *, key=None):
    return client.post(
        "/api/v1" + path,
        json=body,
        headers={"Idempotency-Key": key or str(uuid4())},
    )


def save(client, total=400, count=4):
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


def get_preview(client, commitment, shares):
    response = client.post(
        f"/api/v1/commitments/{commitment['id']}/responsibility-preview",
        json={"version": commitment["version"], "shares": shares},
    )
    assert response.status_code == 200
    return response.json()


def apply(client, commitment_id, preview, shares, *, key=None):
    return write(
        client,
        f"/commitments/{commitment_id}/responsibility",
        {
            "source_version": preview["source_version"],
            "preview_hash": preview["preview_hash"],
            "shares": shares,
        },
        key=key,
    )


def test_transfer_changes_two_open_keeps_two_paid_reopens_and_audits(client, engine):
    commitment = save(client)
    pay(client, commitment["installments"][0])
    pay(client, commitment["installments"][1])
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    december_closure = str(uuid4())
    january_closure = str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO month_closures"
                "(id,family_id,version,created_at,month,closed) VALUES "
                "(:december,:family,1,now(),'2026-12-01',true),"
                "(:january,:family,1,now(),'2027-01-01',true)"
            ),
            {
                "family": client.family_id,
                "december": december_closure,
                "january": january_closure,
            },
        )
    shares = [{"user_id": client.other_id, "weight": 200}]
    preview = get_preview(client, current, shares)
    key = str(uuid4())

    response = apply(client, commitment["id"], preview, shares, key=key)

    assert response.status_code == 200
    body = response.json()
    assert [part["shares"] for part in body["installments"][:2]] == [
        [{"user_id": client.user_id, "weight": 100, "position": 0}],
        [{"user_id": client.user_id, "weight": 100, "position": 0}],
    ]
    assert [part["shares"] for part in body["installments"][2:]] == [
        [{"user_id": client.other_id, "weight": 100, "position": 0}],
        [{"user_id": client.other_id, "weight": 100, "position": 0}],
    ]
    assert [part["paid_at"] for part in body["installments"]] == [
        "2026-10-05",
        "2026-10-05",
        None,
        None,
    ]
    assert apply(client, commitment["id"], preview, shares, key=key).json() == body
    with engine.connect() as connection:
        assert connection.execute(
            text(
                "SELECT month,closed FROM month_closures "
                "WHERE family_id=:family ORDER BY month"
            ),
            {"family": client.family_id},
        ).all() == [
            (date(2026, 12, 1), False),
            (date(2027, 1, 1), False),
        ]
        audit = connection.execute(
            text(
                "SELECT actor_id,operation,entity_id,details FROM audit_events "
                "WHERE entity_id=:id ORDER BY created_at DESC LIMIT 1"
            ),
            {"id": commitment["id"]},
        ).one()
    assert audit.actor_id == client.user_id
    assert audit.operation == "transfer_responsibility"
    assert audit.entity_id == commitment["id"]
    assert audit.details["fields"] == ["responsibility"]
    assert audit.details["installment_ids"] == [part["id"] for part in body["installments"][2:]]


def test_change_after_preview_rejects_everything(client):
    commitment = save(client, 200, 2)
    shares = [{"user_id": client.other_id, "weight": 200}]
    preview = get_preview(client, commitment, shares)
    pay(client, commitment["installments"][0])

    response = apply(client, commitment["id"], preview, shares)

    assert response.status_code == 409
    assert response.json()["code"] == "version_conflict"
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    assert current["installments"][0]["shares"][0]["user_id"] == client.user_id
    assert current["installments"][1]["shares"][0]["user_id"] == client.user_id


def test_hash_mismatch_and_intermediate_failure_do_not_partially_apply(client, monkeypatch):
    commitment = save(client, 200, 2)
    shares = [{"user_id": client.other_id, "weight": 200}]
    preview = get_preview(client, commitment, shares)
    wrong = {**preview, "preview_hash": "0" * 64}
    mismatch = apply(client, commitment["id"], wrong, shares)
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "version_conflict"

    original = commitment_changes.replace_open_snapshots

    def fail_after_delete(db, family, preview_data):
        original(db, family, preview_data)
        raise RuntimeError("induced rollback")

    monkeypatch.setattr(commitment_changes, "replace_open_snapshots", fail_after_delete)
    with pytest.raises(RuntimeError, match="induced rollback"):
        apply(client, commitment["id"], preview, shares)
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    assert [part["shares"][0]["user_id"] for part in current["installments"]] == [
        client.user_id,
        client.user_id,
    ]


def test_planned_advance_uses_transferred_open_snapshots(client):
    commitment = save(client, 300, 3)
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
    shares = [{"user_id": client.other_id, "weight": 280}]
    preview = get_preview(client, current, shares)

    response = apply(client, commitment["id"], preview, shares)

    assert response.status_code == 200
    october = client.get(f"/api/v1/months/2026-10?person_id={client.other_id}").json()
    assert october["totals"] == {"expected": 280, "paid": 0, "remaining": 280}
    states = [item["advance_state"] for item in october["items"]]
    assert states.count("planned") == 2
    assert states.count(None) == 1
    assert client.get(f"/api/v1/months/2026-10?person_id={client.user_id}").json()[
        "items"
    ] == []
