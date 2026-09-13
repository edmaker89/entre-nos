"""EDIT-02 AC2/AC3/AC7: transactional full and partial commitment edits."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.api import commitment_changes
from test_commitment_edit_preview import edit_body, preview, save, write
from test_commitments import create_card


def apply(client, commitment, preview_body, edit, *, key=None):
    return client.patch(
        f"/api/v1/commitments/{commitment['id']}",
        json={**edit, "preview_hash": preview_body["preview_hash"]},
        headers={"Idempotency-Key": key or str(uuid4())},
    )


def test_unpaid_full_edit_rebuilds_schedule_snapshots_and_audits(client, engine):
    commitment = save(client)
    card_id = create_card(client)
    edit = edit_body(
        commitment,
        description="Notebook",
        category="Trabalho",
        buyer_id=client.user_id,
        card_id=card_id,
        purchased_at="2026-11-20",
        total_cents=303,
        count=3,
        first_month="2026-12-01",
        shares=[{"user_id": client.other_id, "weight": 303}],
    )
    shown = preview(
        client,
        commitment,
        **{key: value for key, value in edit.items() if key != "version"},
    ).json()
    key = str(uuid4())

    response = apply(client, commitment, shown, edit, key=key)

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Notebook"
    assert body["category"] == "Trabalho"
    assert body["buyer_id"] == client.user_id
    assert body["card_id"] == card_id
    assert body["total_cents"] == 303
    assert body["original_count"] == 3
    assert [part["amount_cents"] for part in body["installments"]] == [101, 101, 101]
    assert [part["month"] for part in body["installments"]] == [
        "2026-12-01",
        "2027-01-01",
        "2027-02-01",
    ]
    assert all(part["shares"] == [{"user_id": client.other_id, "weight": 101, "position": 0}] for part in body["installments"])
    assert not {part["id"] for part in commitment["installments"]} & {
        part["id"] for part in body["installments"]
    }
    assert apply(client, commitment, shown, edit, key=key).json() == body
    with engine.connect() as connection:
        old_count = connection.scalar(
            text("SELECT count(*) FROM installments WHERE commitment_id=:id AND id = ANY(:ids)"),
            {"id": commitment["id"], "ids": [part["id"] for part in commitment["installments"]]},
        )
        audit = connection.execute(
            text("SELECT actor_id,details FROM audit_events WHERE entity_id=:id ORDER BY created_at DESC LIMIT 1"),
            {"id": commitment["id"]},
        ).one()
    assert old_count == 0
    assert audit.actor_id == client.user_id
    assert set(audit.details["fields"]) == {
        "description",
        "category",
        "buyer_id",
        "card_id",
        "purchased_at",
        "total_cents",
        "count",
        "first_month",
        "shares",
    }


def test_partial_paid_edit_changes_only_description_category_and_keeps_obligations(client):
    commitment = save(client)
    first = commitment["installments"][0]
    assert write(
        client,
        f"/installments/{first['id']}/pay",
        {"version": first["version"], "paid_at": "2026-10-05"},
    ).status_code == 200
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    edit = edit_body(current, description="Mercado", category="Alimentação")
    shown = preview(client, current, description="Mercado", category="Alimentação").json()

    response = apply(client, current, shown, edit)

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Mercado"
    assert body["category"] == "Alimentação"
    assert [part["id"] for part in body["installments"]] == [
        part["id"] for part in current["installments"]
    ]
    assert body["installments"][0]["paid_at"] == "2026-10-05"
    assert [part["shares"] for part in body["installments"]] == [
        part["shares"] for part in current["installments"]
    ]


def test_full_edit_cancels_planned_advance_before_rebuild(client, engine):
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
    ).json()
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    edit = edit_body(current, total_cents=400, count=4, shares=[{"user_id": client.user_id, "weight": 400}])
    shown = preview(client, current, total_cents=400, count=4, shares=edit["shares"]).json()

    response = apply(client, current, shown, edit)

    assert response.status_code == 200
    assert [part["amount_cents"] for part in response.json()["installments"]] == [100] * 4
    with engine.connect() as connection:
        state = connection.scalar(text("SELECT state FROM advance_plans WHERE id=:id"), {"id": advance["id"]})
    assert state == "cancelled"


def test_hash_conflict_and_induced_failure_roll_back_every_change(client, monkeypatch, engine):
    commitment = save(client)
    edit = edit_body(commitment, total_cents=300, shares=[{"user_id": client.user_id, "weight": 300}])
    shown = preview(client, commitment, total_cents=300, shares=edit["shares"]).json()
    mismatch = apply(client, commitment, {**shown, "preview_hash": "0" * 64}, edit)
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "version_conflict"

    original = commitment_changes.rebuild_unpaid_commitment

    def fail_after_rebuild(db, family, row, body, preview_data):
        original(db, family, row, body, preview_data)
        raise RuntimeError("induced edit rollback")

    monkeypatch.setattr(commitment_changes, "rebuild_unpaid_commitment", fail_after_rebuild)
    with pytest.raises(RuntimeError, match="induced edit rollback"):
        apply(client, commitment, shown, edit)
    current = client.get(f"/api/v1/commitments/{commitment['id']}").json()
    assert current["total_cents"] == 200
    assert [part["id"] for part in current["installments"]] == [
        part["id"] for part in commitment["installments"]
    ]
    with engine.connect() as connection:
        assert connection.scalar(
            text("SELECT count(*) FROM audit_events WHERE entity_id=:id"),
            {"id": commitment["id"]},
        ) == 0
