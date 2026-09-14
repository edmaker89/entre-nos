from app.api.month_closure import router as closure_router
from app.api.months import router as months_router
from app.api.advance_changes import router as advance_changes_router
from app.api.advances import router as advances_router
from app.api.payments import router as payments_router
from app.api.recurrences import router as recurrences_router
from app.api.cycles import router as cycles_router
from app.api.commitment_changes import router as changes_router
from app.api.imports import router as imports_router
from app.api.commitments import router as commitments_router
from app.api.cards import router as cards_router
from app.api.family import router as family_router
from app.api.family_invites import router as family_invites_router
from app.api.invite_auth import router as invite_auth_router
from app.api.profile import router as profile_router
from app.api.password_reset import router as password_reset_router
from app.errors import AppError
from app.api.auth import router as auth_router
import logging
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.db.unit_of_work import engine

app = FastAPI(title="Expense Flow", version="0.1.0")
logger = logging.getLogger("expense")


@app.exception_handler(SQLAlchemyError)
def handle_database_error(request: Request, exc: SQLAlchemyError):
    operation_id = str(uuid4())
    logger.error("database_error operation_id=%s", operation_id)
    return JSONResponse(
        status_code=503,
        content={
            "code": "database_unavailable",
            "message": "Não foi possível confirmar a gravação. Tente novamente.",
            "operation_id": operation_id,
        },
    )


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content={"code": exc.code, "message": exc.message, "operation_id": str(uuid4()),
                 **({"fields": exc.fields} if exc.fields else {}),
                 **({"difference_cents": exc.difference_cents} if exc.difference_cents is not None else {})},
    )


@app.exception_handler(RequestValidationError)
def handle_validation(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation",
            "message": "Revise os campos informados.",
            "fields": [".".join(str(p) for p in e["loc"]) for e in exc.errors()],
            "operation_id": str(uuid4()),
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def readiness():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok", "email_provider": settings.email_provider}


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(auth_router)
app.include_router(family_router)
app.include_router(family_invites_router)
app.include_router(invite_auth_router)
app.include_router(profile_router)
app.include_router(password_reset_router)

app.include_router(cards_router)

app.include_router(imports_router)
app.include_router(commitments_router)

app.include_router(changes_router)

app.include_router(cycles_router)

app.include_router(recurrences_router)

app.include_router(payments_router)

app.include_router(advances_router)

app.include_router(advance_changes_router)

app.include_router(months_router)

app.include_router(closure_router)
