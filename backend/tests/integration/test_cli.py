"""T6/FAM-01/AUTH-01: provision accounts and revoke existing sessions."""

from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.cli import provision, reset_password
from app.db.models import User, Membership, Session as LoginSession
from app.api.auth import passwords
from app.db.unit_of_work import engine


def test_provision_and_reset():
    email = f"{uuid4()}@test.local"
    family, user = provision("Casa", "Douglas", email, "strong-password")
    with Session(engine) as s, s.begin():
        assert s.get(User, user).email == email
        assert s.get(Membership, (family, user)).role == "owner"
        s.add(LoginSession(user_id=user, token_hash=str(uuid4()), csrf_hash="csrf"))
    with pytest.raises(ValueError, match="cadastrado"):
        provision("Casa", "Douglas", email, "strong-password")
    reset_password(email, "another-password")
    with Session(engine) as s:
        assert passwords.verify(s.get(User, user).password_hash, "another-password") is True
        assert all(
            row.revoked
            for row in s.scalars(select(LoginSession).where(LoginSession.user_id == user))
        )
    other = f"{uuid4()}@test.local"
    second_family, second_user = provision("Casa", "Vanessa", other, "strong-password", family)
    assert second_family == family
    assert second_user != user
    with Session(engine) as s:
        assert s.get(Membership, (family, second_user)).role == "member"
