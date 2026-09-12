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


def account_without_family():
    token = str(uuid4())
    with Session(engine) as s, s.begin():
        user = User(
            email=f"{token}@test.local",
            name="Convidado",
            password_hash=passwords.hash("testing-password"),
        )
        s.add(user)
        s.flush()
        return user.email, user.id


def login(client, email):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testing-password"}
    )


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


def test_user_without_family_can_keep_session_and_fetch_csrf():
    email, user_id = account_without_family()
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        response = login(client, email)
        assert response.status_code == 200
        assert response.json()["user"]["id"] == user_id
        csrf = client.get("/api/v1/auth/csrf")
        assert csrf.status_code == 200
        assert len(csrf.json()["csrf_token"]) == 64


def test_user_without_family_can_logout_with_csrf():
    email, _ = account_without_family()
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        csrf = login(client, email).json()["csrf_token"]
        response = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
        assert response.status_code == 200
        assert response.json() == {"ok": True}


def test_financial_route_still_requires_a_family():
    email, _ = account_without_family()
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        login(client, email)
        response = client.get("/api/v1/cards")
        assert response.status_code == 403
        assert response.json()["code"] == "family_required"


def test_exactly_one_membership_resolves_family_context():
    email, user_id = account()
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        login(client, email)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["user"]["id"] == user_id
        assert response.json()["family_id"]


def test_multiple_memberships_are_rejected_instead_of_selecting_first():
    email, user_id = account()
    with Session(engine) as session, session.begin():
        second = Family(name="Second family")
        session.add(second)
        session.flush()
        session.add(Membership(user_id=user_id, family_id=second.id))
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        login(client, email)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 409
        assert response.json()["code"] == "multiple_families"


def test_current_user_keeps_csrf_protection_without_family():
    email, _ = account_without_family()
    with TestClient(app, client=(str(uuid4()), 123)) as client:
        login(client, email)
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 403
        assert response.json()["code"] == "csrf"
