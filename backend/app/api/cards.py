from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import serialize, get_row, member, operation
from app.db.models import Card
from app.db.unit_of_work import check_version
from app.domain.card_catalog import (
    CARD_INSTITUTIONS,
    CARD_NETWORKS,
    institution_label,
    normalize_institution,
    normalize_network,
    serialize_catalog,
)
from app.errors import AppError

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])


class CardInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    institution_key: str | None = Field(default=None, max_length=40)
    institution: str | None = Field(default=None, max_length=100)
    network: str | None = Field(default=None, max_length=30)
    last_four: str | None = Field(default=None, pattern=r"^[0-9]{4}$")
    holder_id: str
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)

    @model_validator(mode="before")
    @classmethod
    def reject_sensitive_fields(cls, value):
        if isinstance(value, dict) and {"pan", "cvv", "card_number", "number"} & value.keys():
            raise AppError(
                "unsupported_card_data",
                "Informe somente o apelido do cartão e, opcionalmente, os últimos quatro dígitos.",
                422,
            )
        return value

    @field_validator("network", mode="before")
    @classmethod
    def validate_network(cls, value):
        return normalize_network(value)

    @model_validator(mode="after")
    def normalize_institution_fields(self):
        if self.institution_key is None:
            self.institution_key = normalize_institution(self.institution or "")
        else:
            self.institution_key = normalize_institution(self.institution_key)
        if self.institution_key == "other":
            if not self.institution:
                raise ValueError("Informe o nome da outra instituição.")
        else:
            self.institution = institution_label(self.institution_key)
        return self


class CardEdit(CardInput):
    version: int = Field(ge=1)


@router.get("/catalog")
def catalog():
    return {
        "institutions": serialize_catalog(CARD_INSTITUTIONS),
        "networks": serialize_catalog(CARD_NETWORKS),
    }


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
