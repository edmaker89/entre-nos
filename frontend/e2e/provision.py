"""Isolated browser-test household and loopback login window, on a disposable DB only."""
import os
import sys
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.cli import provision
from app.config import settings
from app.api.auth import digest
from app.db.models import LoginWindow
from app.db.unit_of_work import engine

default_dev = settings.database_url.startswith(
    "postgresql+psycopg://expense:expense_dev@localhost:55432/"
)
explicit_isolated = os.environ.get("E2E_ISOLATED_DATABASE") == "1" and ":55432/" not in settings.database_url
if not (default_dev or explicit_isolated):
    raise RuntimeError("Browser fixtures require an explicitly isolated database")
family, _ = provision("Teste navegador", "Douglas", sys.argv[1], sys.argv[2])
provision("Teste navegador", "Vanessa", "v-" + sys.argv[1], sys.argv[2], family)
# Each test starts a new browser/origin fixture. AUTH integration tests separately
# assert the real 11th-attempt rejection; the production limiter is unchanged.
with Session(engine) as session, session.begin():
    session.execute(delete(LoginWindow).where(LoginWindow.origin.in_([digest("127.0.0.1"), digest("::1")])))
