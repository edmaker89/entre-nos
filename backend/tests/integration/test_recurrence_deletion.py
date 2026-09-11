"""REC AC01–03: explicit deletion of mistaken recurrence, with payment protection."""

from uuid import uuid4
from sqlalchemy import select
from app.db.models import Recurrence, Occurrence
from app.db.unit_of_work import transaction


def create(client):
    response = client.post(
        "/api/v1/recurrences",
        json={
            "description": "Aluguel errado",
            "amount_cents": 160000,
            "due_day": 5,
            "start_month": "2026-10-01",
            "shares": [{"user_id": client.user_id, "weight": 1}],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 200
    row = client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json()[0]
    return row


def remove(client, row, **kwargs):
    return client.delete(
        f"/api/v1/recurrences/{row['id']}",
        params={"version": row["version"], "confirm": True, **kwargs},
        headers={"Idempotency-Key": str(uuid4())},
    )


def test_delete_requires_confirmation_and_soft_deletes_all_occurrences(client, engine):
    row = create(client)
    assert remove(client, row, confirm=False).status_code == 409
    assert client.get("/api/v1/months/2026-10").json()["totals"]["expected"] == 160000
    assert remove(client, row, version=99).status_code == 409
    assert remove(client, row).json() == {"ok": True}
    assert client.get("/api/v1/recurrences?from_month=2026-10-01&months=3").json() == []
    assert [
        m["totals"]["expected"]
        for m in client.get("/api/v1/forecast?from_month=2026-10&months=3").json()
    ] == [0, 0, 0]
    with transaction(client.family_id, engine) as db:
        assert db.get(Recurrence, row["id"]).deleted_at is not None
        assert all(
            o.deleted_at is not None
            for o in db.scalars(select(Occurrence).where(Occurrence.recurrence_id == row["id"]))
        )


def test_paid_occurrence_blocks_delete_until_explicit_reopen(client):
    row = create(client)
    occurrence = row["occurrences"][0]
    paid = client.post(
        f"/api/v1/occurrences/{occurrence['id']}/pay",
        json={"version": occurrence["version"], "paid_at": "2026-10-05"},
        headers={"Idempotency-Key": str(uuid4())},
    ).json()
    rejected = remove(client, row)
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "paid"
    assert client.get("/api/v1/months/2026-10").json()["totals"] == {
        "expected": 160000,
        "paid": 160000,
        "remaining": 0,
    }
    assert (
        client.post(
            f"/api/v1/occurrences/{occurrence['id']}/reopen",
            json={"version": paid["version"]},
            headers={"Idempotency-Key": str(uuid4())},
        ).status_code
        == 200
    )
    assert remove(client, row).status_code == 200
    assert client.get("/api/v1/months/2026-10").json()["totals"] == {
        "expected": 0,
        "paid": 0,
        "remaining": 0,
    }
