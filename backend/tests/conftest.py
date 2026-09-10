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
