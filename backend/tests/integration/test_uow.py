"""DATA-01 AC02–05 / BUY-01 AC06 / ADV-01 AC09."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Family, MonthClosure
from app.db.unit_of_work import transaction, mutate, check_version
from app.main import AppError


def test_rollback_and_idempotency(engine):
    family = str(uuid4())
    with Session(engine) as s, s.begin():
        s.add(Family(id=family, name="transaction test"))

    def change(s):
        s.add(MonthClosure(family_id=family, month=__import__("datetime").date(2026, 10, 1)))
        s.flush()
        return {"amount_cents": 10000}

    with pytest.raises(RuntimeError):
        with transaction(family, engine) as s:
            mutate(s, family, "failure", {"amount": 10000}, lambda: change(s))
            raise RuntimeError("rollback")
    with transaction(family, engine) as s:
        assert s.scalars(select(MonthClosure)).all() == []
        assert mutate(s, family, "key", {"amount": 10000}, lambda: change(s)) == {
            "amount_cents": 10000
        }
    with transaction(family, engine) as s:
        assert mutate(s, family, "key", {"amount": 10000}, lambda: change(s)) == {
            "amount_cents": 10000
        }
        assert len(s.scalars(select(MonthClosure)).all()) == 1
        with pytest.raises(AppError, match="conteúdo diferente"):
            mutate(s, family, "key", {"amount": 20000}, lambda: change(s))


def test_concurrent_updates_only_first_wins(engine):
    family, closure = str(uuid4()), str(uuid4())
    with Session(engine) as s, s.begin():
        s.add(Family(id=family, name="concurrent"))
        s.flush()
        s.add(
            MonthClosure(
                id=closure, family_id=family, month=__import__("datetime").date(2026, 10, 1)
            )
        )

    def update():
        try:
            with transaction(family, engine) as s:
                row = s.get(MonthClosure, closure)
                check_version(row, 1)
                row.closed = False
            return "saved"
        except AppError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: update(), range(2))) == ["conflict", "saved"]
    with transaction(family, engine) as s:
        row = s.get(MonthClosure, closure)
        assert (row.version, row.closed) == (2, False)


def test_database_error_log_does_not_leak_payload(engine, caplog):
    from sqlalchemy import text

    with pytest.raises(AppError) as error:
        with transaction("missing", engine) as s:
            s.execute(text("SELECT 'secret-financial-value'::integer"))
    assert error.value.status == 404
    # Use an existing family to reach a real driver failure.
    family = str(uuid4())
    with Session(engine) as s, s.begin():
        s.add(Family(id=family, name="failure"))
    with pytest.raises(AppError) as error:
        with transaction(family, engine) as s:
            s.execute(text("SELECT 'secret-financial-value'::integer"))
    assert error.value.status == 503
    assert "database_error operation_id=" in caplog.text
    assert "secret-financial-value" not in caplog.text


def test_route_database_failure_is_sanitized_and_rolled_back(client, caplog):
    """DATA AC05: errors at the real route transaction boundary are sanitized."""
    from sqlalchemy import event, text
    from app.db.models import Card

    def fail_commit(session):
        if session.scalar(select(Card).where(Card.name == "private-purchase-secret-191900")):
            session.execute(text("SELECT 'private-purchase-secret-191900'::integer"))

    event.listen(Session, "before_commit", fail_commit)
    try:
        result = client.post(
            "/api/v1/cards",
            json={"name": "private-purchase-secret-191900", "institution": "Test", "holder_id": client.user_id,
                  "closing_day": 25, "due_day": 5},
            headers={"Idempotency-Key": str(uuid4())},
        )
    finally:
        event.remove(Session, "before_commit", fail_commit)
    assert result.status_code == 503
    payload = result.json()
    assert payload["code"] == "database_unavailable"
    assert payload["operation_id"] in caplog.text
    assert "database_error" in caplog.text
    assert "private-purchase-secret-191900" not in caplog.text + result.text
    assert client.get("/api/v1/cards").json() == []
