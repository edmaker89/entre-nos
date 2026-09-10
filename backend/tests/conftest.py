import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import settings


@pytest.fixture
def engine():
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection) as session:
            yield session
        transaction.rollback()


@pytest.fixture
def client():
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from app.cli import provision
    from app.main import app

    email = f"{uuid4()}@test.local"
    family, user = provision("Test", "Douglas", email, "testing-password")
    _, other = provision("Test", "Vanessa", f"{uuid4()}@test.local", "testing-password", family)
    with TestClient(app, client=(str(uuid4()), 123)) as c:
        result = c.post("/api/v1/auth/login", json={"email": email, "password": "testing-password"})
        c.headers["X-CSRF-Token"] = result.json()["csrf_token"]
        c.user_id = user
        c.other_id = other
        c.family_id = family
        yield c
