from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import serialize, get_row, member, operation
from app.db.models import Card
from app.db.unit_of_work import check_version

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


class CardInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    institution: str = Field(min_length=1, max_length=200)
    holder_id: str
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)


class CardEdit(CardInput):
    version: int = Field(ge=1)


@router.get("")
def listing(db: DB, family: FamilyID):
    return [
        serialize(c)
        for c in db.scalars(select(Card).where(Card.deleted_at.is_(None)).order_by(Card.name))
    ]


@router.post("")
def create(body: CardInput, request: Request, db: DB, family: FamilyID):
    def action():
        member(db, family, body.holder_id)
        card = Card(family_id=family, **body.model_dump())
        db.add(card)
        db.flush()
        return serialize(card)

    return operation(db, family, request, body.model_dump(), action)


@router.patch("/{id}")
def edit(id: str, body: CardEdit, request: Request, db: DB, family: FamilyID):
    def action():
        card = get_row(db, Card, id)
        check_version(card, body.version)
        member(db, family, body.holder_id)
        for key, value in body.model_dump(exclude={"version"}).items():
            setattr(card, key, value)
        db.flush()
        return serialize(card)

    return operation(db, family, request, body.model_dump(), action)
