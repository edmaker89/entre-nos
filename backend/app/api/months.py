from datetime import date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Query
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import member
from app.api.recurrences import materialize
from app.db.models import (
    Commitment,
    Installment,
    InstallmentResponsibilityShare,
    Occurrence,
    OccurrenceResponsibilityShare,
    Recurrence,
    Advance,
    AdvanceItem,
    MonthClosure,
    User,
    Membership,
    now,
)
from app.domain.money import allocate
from app.domain.cycles import month_start, add_months
from app.domain.month_selection import default_month
from app.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["months"])


def parse_month(value):
    try:
        if len(value) != 7:
            raise ValueError()
        return date.fromisoformat(value + "-01")
    except ValueError:
        raise AppError("validation", "Competência deve estar no formato AAAA-MM.", 422) from None


def month_data(db, family, month, person=None):
    materialize(db, family, month, 1)
    if person:
        member(db, family, person)
    names = dict(
        db.execute(
            select(User.id, User.name)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.family_id == family)
        ).all()
    )
    installment_shares = {}
    for snapshot in db.scalars(
        select(InstallmentResponsibilityShare).order_by(
            InstallmentResponsibilityShare.installment_id,
            InstallmentResponsibilityShare.position,
        )
    ):
        installment_shares.setdefault(snapshot.installment_id, []).append(
            {"user_id": snapshot.user_id, "weight": snapshot.weight}
        )
    occurrence_shares = {}
    for snapshot in db.scalars(
        select(OccurrenceResponsibilityShare).order_by(
            OccurrenceResponsibilityShare.occurrence_id,
            OccurrenceResponsibilityShare.position,
        )
    ):
        occurrence_shares.setdefault(snapshot.occurrence_id, []).append(
            {"user_id": snapshot.user_id, "weight": snapshot.weight}
        )
    advances = {
        i.installment_id: (a.id, a.state)
        for i, a in db.execute(
            select(AdvanceItem, Advance)
            .join(Advance, Advance.id == AdvanceItem.advance_id)
            .where(Advance.state != "cancelled")
        )
    }
    items = []
    for p, c in db.execute(
        select(Installment, Commitment)
        .join(Commitment, Commitment.id == Installment.commitment_id)
        .where(
            Installment.month == month,
            Installment.deleted_at.is_(None),
            Commitment.deleted_at.is_(None),
        )
    ):
        advance = advances.get(p.id)
        items.append(
            {
                "id": p.id,
                "commitment_id": c.id,
                "description": c.description,
                "kind": "installment",
                "number": p.number,
                "original_count": c.original_count,
                "amount_cents": p.amount_cents,
                "original_cents": p.original_cents,
                "original_month": p.original_month.isoformat(),
                "due_date": p.due_date.isoformat(),
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "cycle_id": p.cycle_id,
                "card_id": c.card_id,
                "version": p.version,
                "estimated": False,
                "needs_review": p.needs_review,
                "advance_id": advance[0] if advance else None,
                "advance_state": advance[1] if advance else None,
                "shares": installment_shares.get(p.id, []),
            }
        )
    for o, r in db.execute(
        select(Occurrence, Recurrence)
        .join(Recurrence, Recurrence.id == Occurrence.recurrence_id)
        .where(Occurrence.month == month, Occurrence.deleted_at.is_(None))
    ):
        items.append(
            {
                "id": o.id,
                "description": r.description,
                "kind": "occurrence",
                "amount_cents": o.amount_cents,
                "due_date": o.due_date.isoformat(),
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                "version": o.version,
                "estimated": o.estimated,
                "shares": occurrence_shares.get(o.id, []),
                "cycle_id": None,
                "card_id": None,
            }
        )
    family_total = sum(i["amount_cents"] for i in items)
    people = {id: 0 for id in names}
    visible = []
    for item in items:
        portions = allocate(item["amount_cents"], [s["weight"] for s in item["shares"]])
        splits = [
            {
                "user_id": s["user_id"],
                "name": names.get(s["user_id"], "Integrante"),
                "amount_cents": a,
            }
            for s, a in zip(item["shares"], portions)
        ]
        for split in splits:
            people[split["user_id"]] = people.get(split["user_id"], 0) + split["amount_cents"]
        item["shares"] = splits
        item["display_cents"] = (
            next((s["amount_cents"] for s in splits if s["user_id"] == person), 0)
            if person
            else item["amount_cents"]
        )
        if not person or item["display_cents"]:
            visible.append(item)
    expected = sum(i["display_cents"] for i in visible)
    paid = sum(i["display_cents"] for i in visible if i["paid_at"])
    return {
        "month": month.strftime("%Y-%m"),
        "items": sorted(visible, key=lambda x: (x["due_date"], x["description"])),
        "totals": {"expected": expected, "paid": paid, "remaining": expected - paid},
        "family_total": family_total,
        "people": [
            {"id": id, "name": names.get(id, "Integrante"), "amount_cents": amount}
            for id, amount in people.items()
        ],
    }


@router.get("/months/{month}")
def get(month: str, db: DB, family: FamilyID, person_id: str | None = None):
    time = now()
    current = month_start(time.astimezone(ZoneInfo("America/Sao_Paulo")).date())
    current_data = month_data(db, family, current)
    closure = db.scalar(select(MonthClosure).where(MonthClosure.month == current))
    initial = default_month(time, bool(closure and closure.closed))
    selected = parse_month(initial if month == "default" else month)
    result = month_data(db, family, selected, person_id)
    return {
        **result,
        "initial_month": initial,
        "current_month": current.strftime("%Y-%m"),
        "current_remaining": current_data["totals"]["remaining"],
    }


@router.get("/forecast")
def forecast(
    db: DB, family: FamilyID, from_month: str, months: int = Query(default=12, ge=1, le=12)
):
    start = parse_month(from_month)
    return [month_data(db, family, add_months(start, i)) for i in range(months)]
