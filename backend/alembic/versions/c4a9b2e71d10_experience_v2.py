"""experience v2 relational foundations

Revision ID: c4a9b2e71d10
Revises: 84e008d3ef75
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a9b2e71d10"
down_revision: Union[str, Sequence[str], None] = "84e008d3ef75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _financial_columns():
    return (
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
    )


def _enable_family_rls(table: str) -> None:
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO expense_app")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY family_isolation ON {table} "
        "USING (family_id = current_setting('app.family_id', true)) "
        "WITH CHECK (family_id = current_setting('app.family_id', true))"
    )


def upgrade() -> None:
    op.add_column("families", sa.Column("code", sa.String(length=12), nullable=True))
    op.add_column("families", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column(
        "families", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("users", sa.Column("version", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("memberships", sa.Column("role", sa.String(length=10), nullable=True))
    op.add_column(
        "memberships", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.alter_column("cards", "institution", new_column_name="institution_name")
    op.alter_column(
        "cards", "institution_name", existing_type=sa.String(length=200), type_=sa.String(100)
    )
    op.add_column("cards", sa.Column("institution_key", sa.String(length=40), nullable=True))
    op.add_column("cards", sa.Column("network", sa.String(length=30), nullable=True))
    op.add_column("cards", sa.Column("last_four", sa.String(length=4), nullable=True))

    op.execute(
        "UPDATE families SET code = translate(upper(substr(md5(id), 1, 10)), '01', 'YZ'), "
        "version = 1, created_at = now()"
    )
    op.execute("UPDATE users SET version = 1, created_at = now()")
    op.execute("UPDATE memberships SET role = 'member', created_at = now()")
    op.execute(
        """
        DO $$
        DECLARE
            family record;
            candidate_id varchar(36);
            douglas_count integer;
            member_count integer;
        BEGIN
            FOR family IN
                SELECT family_id FROM memberships GROUP BY family_id
            LOOP
                SELECT count(*), count(*) FILTER (WHERE lower(u.name) = 'douglas')
                  INTO member_count, douglas_count
                  FROM memberships m
                  JOIN users u ON u.id = m.user_id
                 WHERE m.family_id = family.family_id;

                IF douglas_count = 1 THEN
                    SELECT m.user_id INTO candidate_id
                      FROM memberships m JOIN users u ON u.id = m.user_id
                     WHERE m.family_id = family.family_id AND lower(u.name) = 'douglas';
                ELSIF member_count = 1 THEN
                    SELECT user_id INTO candidate_id FROM memberships
                     WHERE family_id = family.family_id;
                ELSE
                    RAISE EXCEPTION
                        'Cannot determine a unique owner for family %: expected one Douglas or one member',
                        family.family_id;
                END IF;

                UPDATE memberships SET role = 'owner'
                 WHERE family_id = family.family_id AND user_id = candidate_id;
            END LOOP;
        END $$
        """
    )
    op.execute(
        """
        UPDATE cards
           SET institution_key = CASE
               WHEN lower(unaccent_safe) IN ('nubank', 'nu bank') THEN 'nubank'
               WHEN lower(unaccent_safe) IN ('itau', 'itaú') THEN 'itau'
               WHEN lower(unaccent_safe) = 'bradesco' THEN 'bradesco'
               WHEN lower(unaccent_safe) = 'santander' THEN 'santander'
               WHEN lower(unaccent_safe) IN ('banco do brasil', 'bb') THEN 'bb'
               WHEN lower(unaccent_safe) IN ('caixa', 'caixa economica federal') THEN 'caixa'
               WHEN lower(unaccent_safe) IN ('inter', 'banco inter') THEN 'inter'
               WHEN lower(unaccent_safe) IN ('c6', 'c6 bank') THEN 'c6'
               WHEN lower(unaccent_safe) IN ('btg', 'btg pactual') THEN 'btg'
               WHEN lower(unaccent_safe) = 'xp' THEN 'xp'
               WHEN lower(unaccent_safe) = 'picpay' THEN 'picpay'
               WHEN lower(unaccent_safe) IN ('mercado pago', 'mercadopago') THEN 'mercado_pago'
               WHEN lower(unaccent_safe) = 'neon' THEN 'neon'
               WHEN lower(unaccent_safe) = 'sicoob' THEN 'sicoob'
               WHEN lower(unaccent_safe) = 'sicredi' THEN 'sicredi'
               ELSE 'other'
           END
          FROM (SELECT id, translate(lower(institution_name), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc') AS unaccent_safe FROM cards) normalized
         WHERE cards.id = normalized.id
        """
    )

    op.alter_column("families", "code", nullable=False)
    op.alter_column("families", "version", nullable=False)
    op.alter_column("families", "created_at", nullable=False)
    op.create_unique_constraint("uq_families_code", "families", ["code"])
    op.alter_column("users", "version", nullable=False)
    op.alter_column("users", "created_at", nullable=False)
    op.alter_column("memberships", "role", nullable=False)
    op.alter_column("memberships", "created_at", nullable=False)
    op.create_check_constraint(
        "ck_memberships_role", "memberships", "role IN ('owner', 'member')"
    )
    op.create_index(
        "uq_memberships_one_owner",
        "memberships",
        ["family_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
    )
    op.alter_column("cards", "institution_key", nullable=False)
    op.create_check_constraint(
        "ck_cards_last_four", "cards", "last_four IS NULL OR last_four ~ '^[0-9]{4}$'"
    )

    op.create_table(
        "installment_responsibility_shares",
        sa.Column("installment_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("weight", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *_financial_columns(),
        sa.CheckConstraint("weight > 0", name="ck_installment_share_weight"),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(
            ["installment_id", "family_id"], ["installments.id", "installments.family_id"]
        ),
        sa.ForeignKeyConstraint(
            ["family_id", "user_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installment_id", "user_id"),
    )
    op.create_index(
        "ix_installment_responsibility_shares_family_id",
        "installment_responsibility_shares",
        ["family_id"],
    )
    op.create_index(
        "ix_installment_responsibility_shares_installment_id",
        "installment_responsibility_shares",
        ["installment_id"],
    )
    op.create_index(
        "ix_installment_responsibility_shares_user_id",
        "installment_responsibility_shares",
        ["user_id"],
    )

    op.create_unique_constraint(
        "uq_recurring_occurrences_id_family_id",
        "recurring_occurrences",
        ["id", "family_id"],
    )
    op.create_table(
        "occurrence_responsibility_shares",
        sa.Column("occurrence_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("weight", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        *_financial_columns(),
        sa.CheckConstraint("weight > 0", name="ck_occurrence_share_weight"),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(
            ["occurrence_id", "family_id"],
            ["recurring_occurrences.id", "recurring_occurrences.family_id"],
        ),
        sa.ForeignKeyConstraint(
            ["family_id", "user_id"], ["memberships.family_id", "memberships.user_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("occurrence_id", "user_id"),
    )
    op.create_index(
        "ix_occurrence_responsibility_shares_family_id",
        "occurrence_responsibility_shares",
        ["family_id"],
    )
    op.create_index(
        "ix_occurrence_responsibility_shares_occurrence_id",
        "occurrence_responsibility_shares",
        ["occurrence_id"],
    )
    op.create_index(
        "ix_occurrence_responsibility_shares_user_id",
        "occurrence_responsibility_shares",
        ["user_id"],
    )

    op.create_table(
        "family_invites",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by", sa.String(length=36), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *_financial_columns(),
        sa.ForeignKeyConstraint(["family_id"], ["families.id"]),
        sa.ForeignKeyConstraint(
            ["family_id", "created_by"], ["memberships.family_id", "memberships.user_id"]
        ),
        sa.ForeignKeyConstraint(["used_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_family_invites_family_id", "family_invites", ["family_id"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", sa.String(length=12), nullable=False),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.CheckConstraint(
            "delivery_status IN ('pending', 'sent', 'failed')",
            name="ck_password_reset_delivery_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("operation_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])

    op.create_table(
        "auth_rate_limit_windows",
        sa.Column("scope", sa.String(length=30), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count > 0", name="ck_auth_rate_limit_count"),
        sa.PrimaryKeyConstraint("scope", "key_hash"),
    )

    op.execute(
        """
        INSERT INTO installment_responsibility_shares
            (id, installment_id, user_id, weight, position, family_id, version, created_at)
        SELECT md5(i.id || ':' || s.user_id), i.id, s.user_id, s.weight, s.position,
               i.family_id, 1, now()
          FROM installments i
          JOIN responsibility_shares s
            ON s.commitment_id = i.commitment_id AND s.family_id = i.family_id
         WHERE i.deleted_at IS NULL AND s.deleted_at IS NULL AND s.weight > 0
        """
    )
    op.execute(
        """
        INSERT INTO occurrence_responsibility_shares
            (id, occurrence_id, user_id, weight, position, family_id, version, created_at)
        SELECT md5(o.id || ':' || (share.value->>'user_id')), o.id,
               share.value->>'user_id', (share.value->>'weight')::bigint,
               share.position - 1, o.family_id, 1, now()
          FROM recurring_occurrences o
          JOIN recurring_rules r
            ON r.id = o.recurrence_id AND r.family_id = o.family_id
          CROSS JOIN LATERAL json_array_elements(r.shares) WITH ORDINALITY AS share(value, position)
         WHERE o.deleted_at IS NULL AND r.deleted_at IS NULL
           AND (share.value->>'weight')::bigint > 0
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM installments i
                 WHERE i.deleted_at IS NULL AND NOT EXISTS (
                    SELECT 1 FROM installment_responsibility_shares s
                     WHERE s.installment_id = i.id
                 )
            ) THEN
                RAISE EXCEPTION 'Cannot backfill responsibility for every active installment';
            END IF;
            IF EXISTS (
                SELECT 1 FROM recurring_occurrences o
                 WHERE o.deleted_at IS NULL AND NOT EXISTS (
                    SELECT 1 FROM occurrence_responsibility_shares s
                     WHERE s.occurrence_id = o.id
                 )
            ) THEN
                RAISE EXCEPTION 'Cannot backfill responsibility for every active occurrence';
            END IF;
        END $$
        """
    )

    for table in (
        "installment_responsibility_shares",
        "occurrence_responsibility_shares",
        "family_invites",
    ):
        _enable_family_rls(table)


def downgrade() -> None:
    for table in (
        "family_invites",
        "occurrence_responsibility_shares",
        "installment_responsibility_shares",
    ):
        op.drop_table(table)
    op.drop_constraint(
        "uq_recurring_occurrences_id_family_id",
        "recurring_occurrences",
        type_="unique",
    )
    op.drop_table("auth_rate_limit_windows")
    op.drop_table("password_reset_tokens")

    op.drop_constraint("ck_cards_last_four", "cards", type_="check")
    op.drop_column("cards", "last_four")
    op.drop_column("cards", "network")
    op.drop_column("cards", "institution_key")
    op.alter_column(
        "cards", "institution_name", existing_type=sa.String(length=100), type_=sa.String(200)
    )
    op.alter_column("cards", "institution_name", new_column_name="institution")

    op.drop_index("uq_memberships_one_owner", table_name="memberships")
    op.drop_constraint("ck_memberships_role", "memberships", type_="check")
    op.drop_column("memberships", "created_at")
    op.drop_column("memberships", "role")
    op.drop_column("users", "created_at")
    op.drop_column("users", "version")
    op.drop_constraint("uq_families_code", "families", type_="unique")
    op.drop_column("families", "created_at")
    op.drop_column("families", "version")
    op.drop_column("families", "code")
