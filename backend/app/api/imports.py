from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.api.auth import DB, FamilyID
from app.api.commitments import ShareInput, PurchaseInput, preview_purchase, persist_purchase
from app.api.common import operation
from app.domain.cycles import add_months, month_start
from app.domain.money import MAX_CENTS, allocate

router = APIRouter(prefix="/api/v1/commitments", tags=["import"])


class ImportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str = Field(min_length=1, max_length=200)
    buyer_id: str
    card_id: str | None = None
    first_month: date
    original_count: int = Field(ge=1, le=120)
    numbers: list[int] = Field(min_length=1, max_length=120)
    installment_cents: int = Field(gt=0, le=MAX_CENTS)
    shares: list[ShareInput] = Field(min_length=1)
    due_day: int = Field(default=5, ge=1, le=31)

    @model_validator(mode="after")
    def valid(self):
        if len(set(self.numbers)) != len(self.numbers) or any(
            n < 1 or n > self.original_count for n in self.numbers
        ):
            raise ValueError("Intervalo de parcelas inválido.")
        if self.installment_cents * self.original_count > MAX_CENTS:
            raise ValueError("Valor total excede o limite.")
        if sum(s.weight for s in self.shares) <= 0:
            raise ValueError("Divisão inválida.")
        return self


def prepare(db, family, body):
    total = body.installment_cents * body.original_count
    weights = allocate(total, [s.weight for s in body.shares])
    purchase = PurchaseInput(
        description=body.description,
        buyer_id=body.buyer_id,
        card_id=body.card_id,
        purchased_at=body.first_month,
        first_month=body.first_month,
        total_cents=total,
        count=body.original_count,
        shares=[ShareInput(user_id=s.user_id, weight=w) for s, w in zip(body.shares, weights)],
    )
    preview = preview_purchase(db, family, purchase)
    numbers = sorted(body.numbers)
    from app.domain.cycles import on_day

    preview["installments"] = [
        {
            **preview["installments"][0],
            "number": n,
            "month": add_months(month_start(body.first_month), n - numbers[0]).isoformat(),
            "due_date": on_day(
                add_months(month_start(body.first_month), n - numbers[0]), body.due_day
            ).isoformat(),
            "amount_cents": body.installment_cents,
            "needs_review": False,
        }
        for n in numbers
    ]
    return purchase, preview, numbers


@router.post("/import-preview")
def preview(body: ImportInput, db: DB, family: FamilyID):
    return prepare(db, family, body)[1]


@router.post("/import")
def create(body: ImportInput, request: Request, db: DB, family: FamilyID):
    def action():
        purchase, preview, numbers = prepare(db, family, body)
        return persist_purchase(
            db,
            family,
            purchase,
            preview,
            imported=True,
            numbers=numbers,
            kind="purchase" if body.card_id else "financing",
        )

    return operation(db, family, request, body.model_dump(), action)
