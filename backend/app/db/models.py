from datetime import date, datetime, timezone
from secrets import choice
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


def family_code():
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(choice(alphabet) for _ in range(10))


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)


class Financial(Identity):
    family_id: Mapped[str] = mapped_column(ForeignKey("families.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Family(Identity, Base):
    __tablename__ = "families"
    name: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(12), unique=True, default=family_code)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Identity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Membership(Base):
    __tablename__ = "memberships"
    family_id: Mapped[str] = mapped_column(ForeignKey("families.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(10), default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'member')"),
        Index(
            "uq_memberships_one_owner",
            "family_id",
            unique=True,
            postgresql_where=text("role = 'owner'"),
        ),
    )


class Session(Identity, Base):
    __tablename__ = "sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class LoginWindow(Base):
    __tablename__ = "login_attempt_windows"
    origin: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    count: Mapped[int] = mapped_column(Integer)


class Card(Financial, Base):
    __tablename__ = "cards"
    name: Mapped[str] = mapped_column(String(200))
    institution: Mapped[str] = mapped_column("institution_name", String(100))
    institution_key: Mapped[str] = mapped_column(String(40), default="other")
    network: Mapped[str | None] = mapped_column(String(30))
    last_four: Mapped[str | None] = mapped_column(String(4))
    holder_id: Mapped[str] = mapped_column(String(36))
    closing_day: Mapped[int] = mapped_column(Integer)
    due_day: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        ForeignKeyConstraint(
            ["family_id", "holder_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        CheckConstraint("closing_day BETWEEN 1 AND 31 AND due_day BETWEEN 1 AND 31"),
        CheckConstraint("last_four IS NULL OR last_four ~ '^[0-9]{4}$'"),
    )


class Cycle(Financial, Base):
    __tablename__ = "invoice_cycles"
    card_id: Mapped[str] = mapped_column(String(36))
    month: Mapped[date] = mapped_column(Date)
    closing_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        UniqueConstraint("card_id", "month"),
        ForeignKeyConstraint(["card_id", "family_id"], ["cards.id", "cards.family_id"]),
        CheckConstraint("due_date > closing_date"),
    )


class Commitment(Financial, Base):
    __tablename__ = "commitments"
    description: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="purchase")
    category: Mapped[str | None] = mapped_column(String(100))
    buyer_id: Mapped[str] = mapped_column(String(36))
    card_id: Mapped[str | None] = mapped_column(String(36))
    purchased_at: Mapped[date] = mapped_column(Date)
    total_cents: Mapped[int] = mapped_column(BigInteger)
    original_count: Mapped[int] = mapped_column(Integer)
    imported: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        ForeignKeyConstraint(
            ["family_id", "buyer_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        ForeignKeyConstraint(["card_id", "family_id"], ["cards.id", "cards.family_id"]),
        CheckConstraint("original_count BETWEEN 1 AND 120 AND total_cents > 0"),
    )


class Share(Financial, Base):
    __tablename__ = "responsibility_shares"
    commitment_id: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[str] = mapped_column(String(36))
    weight: Mapped[int] = mapped_column(BigInteger)
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(
            ["commitment_id", "family_id"], ["commitments.id", "commitments.family_id"]
        ),
        ForeignKeyConstraint(
            ["family_id", "user_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        UniqueConstraint("commitment_id", "user_id"),
        CheckConstraint("weight >= 0"),
    )


class Installment(Financial, Base):
    __tablename__ = "installments"
    commitment_id: Mapped[str] = mapped_column(String(36))
    number: Mapped[int] = mapped_column(Integer)
    original_cents: Mapped[int] = mapped_column(BigInteger)
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    original_month: Mapped[date] = mapped_column(Date)
    month: Mapped[date] = mapped_column(Date, index=True)
    original_due: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    original_cycle_id: Mapped[str | None] = mapped_column(String(36))
    cycle_id: Mapped[str | None] = mapped_column(String(36), index=True)
    paid_at: Mapped[date | None] = mapped_column(Date)
    payment_kind: Mapped[str | None] = mapped_column(String(20))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    manually_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        UniqueConstraint("commitment_id", "number"),
        ForeignKeyConstraint(
            ["commitment_id", "family_id"], ["commitments.id", "commitments.family_id"]
        ),
        ForeignKeyConstraint(
            ["cycle_id", "family_id"], ["invoice_cycles.id", "invoice_cycles.family_id"]
        ),
        ForeignKeyConstraint(
            ["original_cycle_id", "family_id"], ["invoice_cycles.id", "invoice_cycles.family_id"]
        ),
        CheckConstraint("number > 0 AND original_cents > 0 AND amount_cents > 0"),
    )


class InstallmentResponsibilityShare(Financial, Base):
    __tablename__ = "installment_responsibility_shares"
    installment_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    weight: Mapped[int] = mapped_column(BigInteger)
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(
            ["installment_id", "family_id"], ["installments.id", "installments.family_id"]
        ),
        ForeignKeyConstraint(
            ["family_id", "user_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        UniqueConstraint("installment_id", "user_id"),
        CheckConstraint("weight > 0"),
    )


class Recurrence(Financial, Base):
    __tablename__ = "recurring_rules"
    description: Mapped[str] = mapped_column(String(200))
    start_month: Mapped[date] = mapped_column(Date)
    end_month: Mapped[date | None] = mapped_column(Date)
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    variable: Mapped[bool] = mapped_column(Boolean, default=False)
    due_day: Mapped[int] = mapped_column(Integer)
    shares: Mapped[list] = mapped_column(JSON)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        CheckConstraint("amount_cents > 0 AND due_day BETWEEN 1 AND 31"),
    )


class Occurrence(Financial, Base):
    __tablename__ = "recurring_occurrences"
    recurrence_id: Mapped[str] = mapped_column(String(36))
    month: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date] = mapped_column(Date)
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    estimated: Mapped[bool] = mapped_column(Boolean)
    paid_at: Mapped[date | None] = mapped_column(Date)
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        ForeignKeyConstraint(
            ["recurrence_id", "family_id"], ["recurring_rules.id", "recurring_rules.family_id"]
        ),
        UniqueConstraint("recurrence_id", "month"),
        CheckConstraint("amount_cents > 0"),
    )


class OccurrenceResponsibilityShare(Financial, Base):
    __tablename__ = "occurrence_responsibility_shares"
    occurrence_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    weight: Mapped[int] = mapped_column(BigInteger)
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        ForeignKeyConstraint(
            ["occurrence_id", "family_id"],
            ["recurring_occurrences.id", "recurring_occurrences.family_id"],
        ),
        ForeignKeyConstraint(
            ["family_id", "user_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        UniqueConstraint("occurrence_id", "user_id"),
        CheckConstraint("weight > 0"),
    )


class FamilyInvite(Financial, Base):
    __tablename__ = "family_invites"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_by: Mapped[str] = mapped_column(String(36))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by: Mapped[str | None] = mapped_column(String(36))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["family_id", "created_by"], ["memberships.family_id", "memberships.user_id"]
        ),
        ForeignKeyConstraint(["used_by"], ["users.id"]),
    )


class PasswordResetToken(Identity, Base):
    __tablename__ = "password_reset_tokens"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String(12), default="pending")
    provider_message_id: Mapped[str | None] = mapped_column(String(200))
    operation_id: Mapped[str] = mapped_column(String(36), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (
        CheckConstraint("delivery_status IN ('pending', 'sent', 'failed')"),
    )


class AuthRateLimitWindow(Base):
    __tablename__ = "auth_rate_limit_windows"
    scope: Mapped[str] = mapped_column(String(30), primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    count: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint("count > 0"),)


class Advance(Financial, Base):
    __tablename__ = "advance_plans"
    commitment_id: Mapped[str] = mapped_column(String(36))
    month: Mapped[date] = mapped_column(Date)
    planned_date: Mapped[date] = mapped_column(Date)
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    state: Mapped[str] = mapped_column(String(20), default="planned")
    __table_args__ = (
        UniqueConstraint("id", "family_id"),
        ForeignKeyConstraint(
            ["commitment_id", "family_id"], ["commitments.id", "commitments.family_id"]
        ),
        CheckConstraint("state IN ('planned', 'paid', 'cancelled') AND amount_cents > 0"),
    )


class AdvanceItem(Financial, Base):
    __tablename__ = "advance_items"
    advance_id: Mapped[str] = mapped_column(String(36))
    installment_id: Mapped[str] = mapped_column(String(36))
    snapshot: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (
        ForeignKeyConstraint(
            ["advance_id", "family_id"], ["advance_plans.id", "advance_plans.family_id"]
        ),
        ForeignKeyConstraint(
            ["installment_id", "family_id"], ["installments.id", "installments.family_id"]
        ),
        UniqueConstraint("advance_id", "installment_id"),
    )


class MonthClosure(Financial, Base):
    __tablename__ = "month_closures"
    month: Mapped[date] = mapped_column(Date)
    closed: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("family_id", "month"),)


class Idempotency(Financial, Base):
    __tablename__ = "idempotency_records"
    key: Mapped[str] = mapped_column(String(200))
    payload_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("family_id", "key"),)


class Audit(Financial, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    operation: Mapped[str] = mapped_column(String(200))
    entity_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
