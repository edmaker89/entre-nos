import hashlib
import hmac
from datetime import datetime, timedelta

from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import AuthRateLimitWindow, now


def opaque_key(value: str, secret: str) -> str:
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def consume(
    db: Session,
    scope: str,
    value: str,
    limit: int,
    window_seconds: int,
    secret: str,
    *,
    at: datetime | None = None,
) -> bool:
    observed_at = at or now()
    key_hash = opaque_key(value, secret)
    cutoff = observed_at - timedelta(seconds=window_seconds)
    statement = (
        insert(AuthRateLimitWindow)
        .values(scope=scope, key_hash=key_hash, started_at=observed_at, count=1)
        .on_conflict_do_update(
            index_elements=[AuthRateLimitWindow.scope, AuthRateLimitWindow.key_hash],
            set_={
                "started_at": case(
                    (AuthRateLimitWindow.started_at <= cutoff, observed_at),
                    else_=AuthRateLimitWindow.started_at,
                ),
                "count": case(
                    (AuthRateLimitWindow.started_at <= cutoff, 1),
                    else_=AuthRateLimitWindow.count + 1,
                ),
            },
        )
        .returning(AuthRateLimitWindow.count)
    )
    count = db.scalar(statement)
    return count <= limit
