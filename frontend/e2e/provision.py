"""Isolated browser-test household and loopback login window, on the dev DB only."""
import sys
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.cli import provision
from app.config import settings
from app.api.auth import digest
from app.db.models import LoginWindow
from app.db.unit_of_work import engine

if not settings.database_url.startswith("postgresql+psycopg://expense:expense_dev@localhost:55432/"):
    raise RuntimeError("Browser fixtures require the dedicated development database")
family, _ = provision("Teste navegador", "Douglas", sys.argv[1], sys.argv[2])
provision("Teste navegador", "Vanessa", "v-" + sys.argv[1], sys.argv[2], family)
# Each test starts a new browser/origin fixture. AUTH integration tests separately
# assert the real 11th-attempt rejection; the production limiter is unchanged.
with Session(engine) as session, session.begin():
    session.execute(delete(LoginWindow).where(LoginWindow.origin.in_([digest("127.0.0.1"), digest("::1")])))
