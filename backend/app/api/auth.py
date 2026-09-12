import hashlib
import secrets
from datetime import timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import settings
from app.api.permissions import resolve_family
from app.db.models import User, Membership, Session as LoginSession, LoginWindow, now
from app.db.unit_of_work import engine
from app.errors import AppError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
passwords = PasswordHasher()
dummy_hash = passwords.hash(secrets.token_urlsafe(24))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def database():
    with Session(engine) as s, s.begin():
        s.execute(text("SET LOCAL ROLE expense_app"))
        yield s


DB = Annotated[Session, Depends(database, scope="function")]


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


def current_user(request: Request, db: DB):
    token = request.cookies.get("expense_session", "")
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == digest(token)))
    time = now()
    if (
        not session
        or session.revoked
        or time - session.created_at >= timedelta(seconds=settings.session_absolute_seconds)
        or time - session.last_seen >= timedelta(seconds=settings.session_idle_seconds)
    ):
        raise AppError("unauthorized", "Entre para continuar.", 401)
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise AppError("unauthorized", "Entre para continuar.", 401)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        csrf = request.headers.get("x-csrf-token", "")
        if (origin and origin != settings.app_origin) or not secrets.compare_digest(
            digest(csrf), session.csrf_hash
        ):
            raise AppError("csrf", "Atualize a página e tente novamente.", 403)
    session.last_seen = time
    request.state.user = user
    request.state.session = session
    return user


CurrentUser = Annotated[User, Depends(current_user, scope="function")]


def current_family(request: Request, db: DB, user: CurrentUser) -> str:
    return resolve_family(request, db, user)


FamilyID = Annotated[str, Depends(current_family, scope="function")]


@router.post("/login")
def login(body: Login, request: Request, response: Response):
    if request.headers.get("origin") not in (None, settings.app_origin):
        raise AppError("csrf", "Origem não permitida.", 403)
    origin = digest(request.client.host)
    with Session(engine) as s, s.begin():
        s.execute(text("SET LOCAL ROLE expense_app"))
        s.execute(
            insert(LoginWindow)
            .values(origin=origin, started_at=now(), count=0)
            .on_conflict_do_nothing()
        )
        window = s.scalar(select(LoginWindow).where(LoginWindow.origin == origin).with_for_update())
        if now() - window.started_at >= timedelta(seconds=60):
            window.started_at = now()
            window.count = 0
        window.count += 1
        limited = window.count > 10
    if limited:
        raise AppError("rate_limit", "Muitas tentativas. Aguarde um minuto.", 429)
    with Session(engine) as s, s.begin():
        s.execute(text("SET LOCAL ROLE expense_app"))
        user = s.scalar(select(User).where(User.email == body.email.strip().lower()))
        try:
            valid = passwords.verify(user.password_hash if user else dummy_hash, body.password)
        except VerificationError:
            valid = False
        if not valid or not user or not user.active:
            raise AppError("invalid_login", "Email ou senha incorretos.", 401)
        token = secrets.token_urlsafe(32)
        csrf = digest(token + ":csrf")
        s.add(LoginSession(user_id=user.id, token_hash=digest(token), csrf_hash=digest(csrf)))
        response.set_cookie(
            "expense_session",
            token,
            httponly=True,
            secure=settings.secure_cookies,
            samesite="lax",
            max_age=settings.session_absolute_seconds,
            path="/",
        )
        response.headers["Cache-Control"] = "no-store"
        return {"user": {"id": user.id, "name": user.name}, "csrf_token": csrf}


@router.get("/me")
def me(request: Request, db: DB, family: FamilyID):
    members = db.execute(
        select(User.id, User.name)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.family_id == family)
    ).all()
    return {
        "user": {"id": request.state.user.id, "name": request.state.user.name},
        "family_id": family,
        "members": [{"id": u.id, "name": u.name} for u in members],
    }


@router.get("/csrf")
def csrf(request: Request, user: CurrentUser):
    return {"csrf_token": digest(request.cookies["expense_session"] + ":csrf")}


@router.post("/logout")
def logout(request: Request, response: Response, user: CurrentUser):
    request.state.session.revoked = True
    response.delete_cookie("expense_session", path="/")
    return {"ok": True}
