"""AUTH-RESET-01 AC6: PostgreSQL-backed atomic windows."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuthRateLimitWindow, now
from app.db.unit_of_work import engine
from app.domain.rate_limits import consume, opaque_key


def test_limit_allows_three_email_requests_and_rejects_fourth(db):
    outcomes = [
        consume(db, "reset_email", "person@example.com", 3, 3600, "secret")
        for _ in range(4)
    ]
    assert outcomes == [True, True, True, False]


def test_window_resets_after_duration(db):
    start = now()
    assert consume(db, "reset_origin", "192.0.2.1", 1, 3600, "secret", at=start) is True
    assert consume(db, "reset_origin", "192.0.2.1", 1, 3600, "secret", at=start + timedelta(seconds=3599)) is False
    assert consume(db, "reset_origin", "192.0.2.1", 1, 3600, "secret", at=start + timedelta(seconds=3600)) is True


def test_database_stores_only_hmac_not_email_or_ip(db):
    email = "private@example.com"
    consume(db, "reset_email", email, 3, 3600, "secret")
    row = db.scalar(select(AuthRateLimitWindow).where(AuthRateLimitWindow.scope == "reset_email"))
    assert row.key_hash == opaque_key(email, "secret")
    assert email not in row.key_hash


def test_scopes_have_independent_counters(db):
    assert consume(db, "reset_email", "same", 1, 3600, "secret") is True
    assert consume(db, "reset_origin", "same", 1, 3600, "secret") is True
    rows = db.scalars(select(AuthRateLimitWindow).where(AuthRateLimitWindow.key_hash == opaque_key("same", "secret"))).all()
    assert {row.scope: row.count for row in rows} == {"reset_email": 1, "reset_origin": 1}


def test_concurrent_consumers_never_exceed_limit():
    source = f"concurrent-{now().timestamp()}"
    barrier = Barrier(4)

    def attempt():
        with Session(engine) as session, session.begin():
            barrier.wait()
            return consume(session, "reset_origin", source, 2, 3600, "secret")

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(4)))
    assert sorted(outcomes) == [False, False, True, True]
    with Session(engine) as session:
        row = session.get(AuthRateLimitWindow, ("reset_origin", opaque_key(source, "secret")))
        assert row.count == 4
