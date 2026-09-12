from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import delete as sql_delete, select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, member, operation, reopen_month
from app.api.commitments import PurchaseInput, ShareInput, details, ensure_cycle, preview_purchase
from app.db.models import (
    Commitment,
    Installment,
    InstallmentResponsibilityShare,
    Advance,
    AdvanceItem,
    Card,
    Cycle,
    Audit,
    now,
)
from app.db.unit_of_work import check_version
from app.domain.cycles import month_start, add_months
from app.domain.money import MAX_CENTS
from app.domain.responsibility import allocate_aggregate_split, responsibility_preview_hash
from app.errors import AppError

router = APIRouter(prefix="/api/v1/commitments", tags=["changes"])


class Shift(BaseModel):
    version: int = Field(ge=1)
    first_month: date


class Edit(BaseModel):
    version: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=200)


class ResponsibilityChange(BaseModel):
    version: int = Field(ge=1)
    shares: list[ShareInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def valid(self):
        if len({share.user_id for share in self.shares}) != len(self.shares):
            raise ValueError("Responsável repetido.")
        if sum(share.weight for share in self.shares) <= 0:
            raise ValueError("Divisão inválida.")
        return self


class ResponsibilityApply(BaseModel):
    source_version: int = Field(ge=1)
    preview_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    shares: list[ShareInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def valid(self):
        ResponsibilityChange(version=self.source_version, shares=self.shares)
        return self


class FullEditInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    version: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=100)
    buyer_id: str
    card_id: str | None = None
    purchased_at: date
    total_cents: int = Field(gt=0, le=MAX_CENTS)
    count: int = Field(ge=1, le=120)
    first_month: date
    shares: list[ShareInput] = Field(min_length=1, max_length=20)


def responsibility_preview_data(db, family, id, body):
    commitment = get_row(db, Commitment, id)
    if commitment.version != body.version:
        raise AppError("version_conflict", "Registro alterado. Recarregue.")
    for share in body.shares:
        member(db, family, share.user_id)
    parts = db.scalars(
        select(Installment)
        .where(
            Installment.commitment_id == id,
            Installment.deleted_at.is_(None),
            Installment.paid_at.is_(None),
        )
        .order_by(Installment.number)
    ).all()
    if not parts:
        raise AppError("no_open_obligations", "Este lançamento não possui parcelas abertas.")
    total = sum(part.amount_cents for part in parts)
    difference = total - sum(share.weight for share in body.shares)
    if difference:
        raise AppError(
            "invalid_split",
            "A divisão deve somar exatamente o total aberto.",
            422,
            fields=["shares"],
            difference_cents=difference,
        )
    snapshots = {}
    for snapshot in db.scalars(
        select(InstallmentResponsibilityShare)
        .where(
            InstallmentResponsibilityShare.installment_id.in_([part.id for part in parts])
        )
        .order_by(
            InstallmentResponsibilityShare.installment_id,
            InstallmentResponsibilityShare.position,
        )
    ):
        snapshots.setdefault(snapshot.installment_id, []).append(
            {"user_id": snapshot.user_id, "weight": snapshot.weight}
        )
    if any(part.id not in snapshots for part in parts):
        raise AppError("invalid_state", "Responsabilidade da parcela não encontrada.")
    matrix = allocate_aggregate_split(
        [part.amount_cents for part in parts],
        [(share.user_id, share.weight) for share in body.shares],
    )
    plans = (
        db.scalars(
            select(Advance)
            .join(AdvanceItem, AdvanceItem.advance_id == Advance.id)
            .where(
                AdvanceItem.installment_id.in_([part.id for part in parts]),
                Advance.state == "planned",
            )
            .order_by(Advance.created_at)
        )
        .unique()
        .all()
    )
    planned_advances = []
    part_order = {part.id: index for index, part in enumerate(parts)}
    for plan in plans:
        ids = db.scalars(
            select(AdvanceItem.installment_id).where(
                AdvanceItem.advance_id == plan.id,
                AdvanceItem.installment_id.in_(part_order),
            )
        ).all()
        planned_advances.append(
            {
                "id": plan.id,
                "month": plan.month.isoformat(),
                "amount_cents": plan.amount_cents,
                "installment_ids": sorted(ids, key=part_order.get),
            }
        )
    installments_preview = [
        {
            "id": part.id,
            "number": part.number,
            "month": part.month.isoformat(),
            "amount_cents": part.amount_cents,
            "version": part.version,
            "before": snapshots[part.id],
            "after": [
                {"user_id": user_id, "weight": weight} for user_id, weight in row
            ],
        }
        for part, row in zip(parts, matrix, strict=True)
    ]
    read_set = {
        "source_version": commitment.version,
        "installments": installments_preview,
        "planned_advances": planned_advances,
        "shares": [share.model_dump() for share in body.shares],
    }
    return {
        **read_set,
        "preview_hash": responsibility_preview_hash(read_set),
        "open_total_cents": total,
        "open_installment_count": len(parts),
        "months": sorted({part.month.strftime("%Y-%m") for part in parts}),
    }


@router.post("/{id}/responsibility-preview")
def responsibility_preview(
    id: str, body: ResponsibilityChange, db: DB, family: FamilyID
):
    return responsibility_preview_data(db, family, id, body)


def replace_open_snapshots(db, family, preview_data):
    installment_ids = [part["id"] for part in preview_data["installments"]]
    db.execute(
        sql_delete(InstallmentResponsibilityShare).where(
            InstallmentResponsibilityShare.installment_id.in_(installment_ids)
        )
    )
    for part in preview_data["installments"]:
        for position, share in enumerate(part["after"]):
            db.add(
                InstallmentResponsibilityShare(
                    family_id=family,
                    installment_id=part["id"],
                    user_id=share["user_id"],
                    weight=share["weight"],
                    position=position,
                )
            )
    db.flush()


@router.post("/{id}/responsibility")
def transfer_responsibility(
    id: str,
    body: ResponsibilityApply,
    request: Request,
    db: DB,
    family: FamilyID,
):
    def action():
        commitment = db.scalar(
            select(Commitment)
            .where(Commitment.id == id, Commitment.deleted_at.is_(None))
            .with_for_update()
        )
        if commitment is None:
            raise AppError("not_found", "Registro não encontrado.", 404)
        preview_data = responsibility_preview_data(
            db,
            family,
            id,
            ResponsibilityChange(version=body.source_version, shares=body.shares),
        )
        if preview_data["preview_hash"] != body.preview_hash:
            raise AppError(
                "version_conflict",
                "A prévia não representa mais as parcelas abertas. Recarregue.",
            )
        check_version(commitment, body.source_version)
        replace_open_snapshots(db, family, preview_data)
        for part in preview_data["installments"]:
            reopen_month(db, family, date.fromisoformat(part["month"]))
        db.add(
            Audit(
                family_id=family,
                actor_id=request.state.user.id,
                operation="transfer_responsibility",
                entity_id=commitment.id,
                details={
                    "fields": ["responsibility"],
                    "installment_ids": [
                        part["id"] for part in preview_data["installments"]
                    ],
                },
            )
        )
        db.flush()
        return details(db, commitment)

    return operation(db, family, request, body.model_dump(), action)


def edit_preview_data(db, family, id, body):
    commitment = get_row(db, Commitment, id)
    if commitment.version != body.version:
        raise AppError("version_conflict", "Registro alterado. Recarregue.")
    current = details(db, commitment)
    parts = current["installments"]
    template_shares = [
        {"user_id": share["user_id"], "weight": share["weight"]}
        for share in current["shares"]
    ]
    requested_shares = [share.model_dump() for share in body.shares]
    recalculation_values = {
        "buyer_id": (commitment.buyer_id, body.buyer_id),
        "card_id": (commitment.card_id, body.card_id),
        "purchased_at": (commitment.purchased_at, body.purchased_at),
        "total_cents": (commitment.total_cents, body.total_cents),
        "count": (commitment.original_count, body.count),
        "first_month": (date.fromisoformat(parts[0]["month"]), month_start(body.first_month)),
        "shares": (template_shares, requested_shares),
    }
    changed_recalculation = [
        field for field, (before, after) in recalculation_values.items() if before != after
    ]
    has_payments = any(part["paid_at"] for part in parts)
    if has_payments and changed_recalculation:
        raise AppError(
            "paid_fields_locked",
            "Há pagamentos. Altere somente descrição e categoria ou reabra-os.",
            fields=changed_recalculation,
        )
    if has_payments:
        schedule = parts
    else:
        purchase = PurchaseInput(**body.model_dump(exclude={"version"}))
        schedule = preview_purchase(db, family, purchase)["installments"]
    before_commitment = {
        "description": commitment.description,
        "category": commitment.category,
        "buyer_id": commitment.buyer_id,
        "card_id": commitment.card_id,
        "purchased_at": commitment.purchased_at.isoformat(),
        "total_cents": commitment.total_cents,
        "count": commitment.original_count,
        "first_month": parts[0]["month"],
        "shares": template_shares,
    }
    after_commitment = {
        "description": body.description,
        "category": body.category,
        "buyer_id": body.buyer_id,
        "card_id": body.card_id,
        "purchased_at": body.purchased_at.isoformat(),
        "total_cents": body.total_cents,
        "count": body.count,
        "first_month": month_start(body.first_month).isoformat(),
        "shares": requested_shares,
    }
    target_months = {date.fromisoformat(part["month"]) for part in schedule}
    current_cycle_ids = {part["cycle_id"] for part in parts if part["cycle_id"]}
    cycle_filters = []
    if current_cycle_ids:
        cycle_filters.append(Cycle.id.in_(current_cycle_ids))
    if body.card_id:
        cycle_filters.append(Cycle.card_id == body.card_id)
    cycles = []
    if cycle_filters:
        from sqlalchemy import or_

        rows = db.scalars(select(Cycle).where(or_(*cycle_filters)).order_by(Cycle.month)).all()
        cycles = [
            {
                "id": cycle.id,
                "month": cycle.month.isoformat(),
                "confirmed": cycle.confirmed,
                "paid_at": cycle.paid_at.isoformat() if cycle.paid_at else None,
            }
            for cycle in rows
            if cycle.id in current_cycle_ids
            or (cycle.card_id == body.card_id and cycle.month in target_months)
        ]
    plans = db.scalars(
        select(Advance)
        .where(Advance.commitment_id == id, Advance.state == "planned")
        .order_by(Advance.created_at)
    ).all()
    planned_advances = []
    part_order = {part["id"]: index for index, part in enumerate(parts)}
    for plan in plans:
        ids = db.scalars(
            select(AdvanceItem.installment_id).where(AdvanceItem.advance_id == plan.id)
        ).all()
        planned_advances.append(
            {
                "id": plan.id,
                "state": plan.state,
                "amount_cents": plan.amount_cents,
                "installment_ids": sorted(ids, key=part_order.get),
            }
        )
    read_set = {
        "source_version": commitment.version,
        "has_payments": has_payments,
        "before": {"commitment": before_commitment, "installments": parts},
        "after": {"commitment": after_commitment, "installments": schedule},
        "affected_cycles": cycles,
        "planned_advances": planned_advances,
    }
    return {
        **read_set,
        "allowed_fields": (
            ["description", "category"]
            if has_payments
            else [
                "description",
                "category",
                "buyer_id",
                "card_id",
                "purchased_at",
                "total_cents",
                "count",
                "first_month",
                "shares",
            ]
        ),
        "preview_hash": responsibility_preview_hash(read_set),
    }


@router.post("/{id}/edit-preview")
def edit_preview(id: str, body: FullEditInput, db: DB, family: FamilyID):
    return edit_preview_data(db, family, id, body)


def editable(db, id):
    c = get_row(db, Commitment, id)
    parts = db.scalars(
        select(Installment)
        .where(Installment.commitment_id == id, Installment.deleted_at.is_(None))
        .order_by(Installment.number)
    ).all()
    if any(p.paid_at for p in parts):
        raise AppError("paid", "Reabra os pagamentos antes de alterar a compra.")
    if db.scalar(
        select(Advance.id).where(Advance.commitment_id == id, Advance.state != "cancelled")
    ):
        raise AppError("active_advance", "Cancele a antecipação antes de reorganizar a compra.")
    return c, parts


def shift_preview(db, id, body):
    c, parts = editable(db, id)
    if c.version != body.version:
        raise AppError("version_conflict", "Registro alterado. Recarregue.")
    first = parts[0].month
    target = month_start(body.first_month)
    offset = (target.year - first.year) * 12 + target.month - first.month
    return c, parts, [add_months(p.month, offset) for p in parts], offset


@router.post("/{id}/preview-shift")
def preview(id: str, body: Shift, db: DB, family: FamilyID):
    c, parts, months, offset = shift_preview(db, id, body)
    return {
        "installments": [
            {"number": p.number, "month": m.isoformat(), "amount_cents": p.amount_cents}
            for p, m in zip(parts, months)
        ]
    }


@router.post("/{id}/shift")
def shift(id: str, body: Shift, request: Request, db: DB, family: FamilyID):
    def action():
        c, parts, months, offset = shift_preview(db, id, body)
        check_version(c, body.version)
        card = get_row(db, Card, c.card_id) if c.card_id else None
        for p, m in zip(parts, months):
            cycle = ensure_cycle(db, family, card, m) if card else None
            p.month = m
            p.due_date = cycle.due_date if cycle else add_months(p.due_date, offset)
            p.cycle_id = cycle.id if cycle else None
            p.manually_assigned = True
            p.version += 1
            if cycle:
                cycle.confirmed = False
                cycle.version += 1
            reopen_month(db, family, m)
        db.flush()
        return details(db, c)

    return operation(db, family, request, body.model_dump(), action)


@router.patch("/{id}")
def edit(id: str, body: Edit, request: Request, db: DB, family: FamilyID):
    def action():
        c, parts = editable(db, id)
        check_version(c, body.version)
        if not body.description.strip():
            raise AppError("validation", "Descrição obrigatória.", 422)
        c.description = body.description.strip()
        db.flush()
        return details(db, c)

    return operation(db, family, request, body.model_dump(), action)


@router.delete("/{id}")
def delete(
    id: str, version: int, request: Request, db: DB, family: FamilyID, confirm: bool = False
):
    def action():
        if not confirm:
            raise AppError("confirmation", "Confirme a exclusão da compra e suas parcelas.")
        c, parts = editable(db, id)
        check_version(c, version)
        c.deleted_at = now()
        for part in parts:
            part.deleted_at = c.deleted_at
        return {"ok": True}

    return operation(db, family, request, {"version": version, "confirm": confirm}, action)
