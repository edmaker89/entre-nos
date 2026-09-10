"""AUTH-01 AC01–05 / FAM-01: real cookie/session lifecycle."""

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import User, Family, Membership, Session as LoginSession, now
from app.db.unit_of_work import engine
from app.main import app
from app.api.auth import passwords


def account():
    token = str(uuid4())
    with Session(engine) as s, s.begin():
        u = User(
            email=f"{token}@test.local",
            name="Douglas",
            password_hash=passwords.hash("testing-password"),
        )
        f = Family(name="Test family")
        s.add_all([u, f])
        s.flush()
        s.add(Membership(user_id=u.id, family_id=f.id))
        return u.email, u.id


def test_cookie_login_csrf_logout():
    email, user = account()
    with TestClient(app, client=(str(uuid4()), 123)) as c:
        r = c.post("/api/v1/auth/login", json={"email": email, "password": "testing-password"})
        assert r.status_code == 200
        assert "HttpOnly" in r.headers["set-cookie"]
        assert "SameSite=lax" in r.headers["set-cookie"]
        assert c.get("/api/v1/auth/me").json()["user"]["id"] == user
        assert c.post("/api/v1/auth/logout").status_code == 403
        csrf = c.get("/api/v1/auth/csrf").json()["csrf_token"]
        assert (
            c.post(
                "/api/v1/auth/logout", headers={"X-CSRF-Token": csrf, "Origin": "https://evil.test"}
            ).status_code
            == 403
        )
        assert c.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
        assert c.get("/api/v1/auth/me").status_code == 401


def test_session_expiry_and_hash_storage():
    email, user = account()
    with TestClient(app, client=(str(uuid4()), 123)) as c:
        c.post("/api/v1/auth/login", json={"email": email, "password": "testing-password"})
        cookie = c.cookies.get("expense_session")
        with Session(engine) as s, s.begin():
            row = s.scalar(select(LoginSession).where(LoginSession.user_id == user))
            assert row.token_hash != cookie
            assert len(row.token_hash) == 64
            row.last_seen = now() - timedelta(hours=25)
        assert c.get("/api/v1/auth/me").status_code == 401
        c.post("/api/v1/auth/login", json={"email": email, "password": "testing-password"})
        with Session(engine) as s, s.begin():
            for row in s.scalars(select(LoginSession).where(LoginSession.user_id == user)):
                row.created_at = now() - timedelta(days=8)
                row.last_seen = now()
        assert c.get("/api/v1/auth/me").status_code == 401


def test_login_rate_limit():
    with TestClient(app, client=(str(uuid4()), 123)) as c:
        for _ in range(10):
            assert (
                c.post(
                    "/api/v1/auth/login", json={"email": "none@test.local", "password": "wrong"}
                ).status_code
                == 401
            )
        assert (
            c.post(
                "/api/v1/auth/login", json={"email": "none@test.local", "password": "wrong"}
            ).status_code
            == 429
        )


def test_secure_cookie_and_activity_preserves_absolute_deadline(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "secure_cookies", True)
    email, user = account()
    with TestClient(app, base_url="https://testserver", client=(str(uuid4()), 123)) as c:
        response = c.post(
            "/api/v1/auth/login", json={"email": email, "password": "testing-password"}
        )
        assert "Secure" in response.headers["set-cookie"]
        with Session(engine) as s, s.begin():
            row = s.scalar(select(LoginSession).where(LoginSession.user_id == user))
            created = row.created_at
            row.last_seen = now() - timedelta(hours=1)
        assert c.get("/api/v1/auth/me").status_code == 200
        with Session(engine) as s:
            row = s.scalar(select(LoginSession).where(LoginSession.user_id == user))
            assert row.created_at == created
            assert now() - row.last_seen < timedelta(seconds=10)


def test_login_window_resets():
    from app.api.auth import digest
    from app.db.models import LoginWindow

    origin = str(uuid4())
    with Session(engine) as s, s.begin():
        s.add(
            LoginWindow(origin=digest(origin), started_at=now() - timedelta(seconds=61), count=11)
        )
    with TestClient(app, client=(origin, 123)) as c:
        assert (
            c.post(
                "/api/v1/auth/login", json={"email": "none@test.local", "password": "wrong"}
            ).status_code
            == 401
        )
