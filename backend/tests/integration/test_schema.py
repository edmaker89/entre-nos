"""Persisted schema, migration backfill, and family isolation."""

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.config import settings


def test_experience_v2_schema_has_required_columns_and_tables(engine):
    schema = inspect(engine)
    tables = set(schema.get_table_names())
    assert {
        "installment_responsibility_shares",
        "occurrence_responsibility_shares",
        "family_invites",
        "password_reset_tokens",
        "auth_rate_limit_windows",
    } <= tables
    assert {"code", "version", "created_at"} <= {
        column["name"] for column in schema.get_columns("families")
    }
    assert {"version", "created_at"} <= {
        column["name"] for column in schema.get_columns("users")
    }
    assert {"role", "created_at"} <= {
        column["name"] for column in schema.get_columns("memberships")
    }
    assert {"institution_key", "institution_name", "network", "last_four"} <= {
        column["name"] for column in schema.get_columns("cards")
    }


def test_experience_v2_constraints_reject_invalid_state(db):
    db.execute(text("INSERT INTO families(id,name,code,version,created_at) VALUES ('f','F','FAMILYCODE',1,now())"))
    db.execute(
        text(
            "INSERT INTO users(id,email,name,password_hash,active,version,created_at) "
            "VALUES ('u1','u1@test','Douglas','hash',true,1,now()),"
            "('u2','u2@test','Vanessa','hash',true,1,now())"
        )
    )
    db.execute(
        text(
            "INSERT INTO memberships(family_id,user_id,role,created_at) "
            "VALUES ('f','u1','owner',now()),('f','u2','member',now())"
        )
    )
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(text("UPDATE memberships SET role='owner' WHERE user_id='u2'"))


def test_snapshot_constraints_reject_zero_weight_and_foreign_member(db):
    db.execute(text("INSERT INTO families(id,name,code,version,created_at) VALUES ('a','A','AAAAAAAABC',1,now()),('b','B','BBBBBBBBBC',1,now())"))
    db.execute(text("INSERT INTO users(id,email,name,password_hash,active,version,created_at) VALUES ('u','u@test','User','hash',true,1,now())"))
    db.execute(text("INSERT INTO memberships(family_id,user_id,role,created_at) VALUES ('a','u','owner',now()),('b','u','member',now())"))
    db.execute(text("INSERT INTO commitments(id,family_id,version,created_at,description,kind,buyer_id,purchased_at,total_cents,original_count,imported) VALUES ('c','a',1,now(),'Purchase','expense','u','2026-09-01',100,1,false)"))
    db.execute(text("INSERT INTO installments(id,family_id,version,created_at,commitment_id,number,original_cents,amount_cents,original_month,month,original_due,due_date,needs_review,manually_assigned) VALUES ('i','a',1,now(),'c',1,100,100,'2026-09-01','2026-09-01','2026-09-01','2026-09-01',false,false)"))
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(text("INSERT INTO installment_responsibility_shares(id,family_id,version,created_at,installment_id,user_id,weight,position) VALUES ('s','a',1,now(),'i','u',0,0)"))
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(text("INSERT INTO installment_responsibility_shares(id,family_id,version,created_at,installment_id,user_id,weight,position) VALUES ('s2','a',1,now(),'i','missing',1,0)"))


def test_family_tables_are_forced_through_rls(engine):
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname = ANY(:tables)"
            ),
            {
                "tables": [
                    "installment_responsibility_shares",
                    "occurrence_responsibility_shares",
                    "family_invites",
                ]
            },
        ).all()
    assert {row.relname for row in rows} == {
        "installment_responsibility_shares",
        "occurrence_responsibility_shares",
        "family_invites",
    }
    assert all(row.relrowsecurity and row.relforcerowsecurity for row in rows)


def test_family_invite_rls_hides_and_blocks_foreign_rows(db):
    db.execute(
        text(
            "INSERT INTO families(id,name,code,version,created_at) VALUES "
            "('a','A','INVITEAAA1',1,now()),('b','B','INVITEBBB2',1,now())"
        )
    )
    db.execute(
        text(
            "INSERT INTO users(id,email,name,password_hash,active,version,created_at) VALUES "
            "('ua','ua@test','A','hash',true,1,now()),"
            "('ub','ub@test','B','hash',true,1,now())"
        )
    )
    db.execute(
        text(
            "INSERT INTO memberships(family_id,user_id,role,created_at) VALUES "
            "('a','ua','owner',now()),('b','ub','owner',now())"
        )
    )
    db.execute(
        text(
            "INSERT INTO family_invites(id,family_id,version,created_at,token_hash,created_by,expires_at) VALUES "
            "('ia','a',1,now(),repeat('a',64),'ua',now() + interval '7 days'),"
            "('ib','b',1,now(),repeat('b',64),'ub',now() + interval '7 days')"
        )
    )
    db.execute(text("SET LOCAL ROLE expense_app"))
    assert db.execute(text("SELECT id FROM family_invites")).all() == []
    db.execute(text("SELECT set_config('app.family_id','a',true)"))
    assert db.execute(text("SELECT id FROM family_invites")).scalars().all() == ["ia"]
    assert db.execute(
        text("UPDATE family_invites SET revoked_at=now() WHERE id='ib' RETURNING id")
    ).all() == []


def test_populated_upgrade_backfills_owner_cards_and_snapshots(engine):
    database_name = f"expense_migration_{uuid4().hex}"
    admin_url = settings.database_url.rsplit("/", 1)[0] + "/postgres"
    test_url = settings.database_url.rsplit("/", 1)[0] + f"/{database_name}"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    admin.connect().execute(text(f'CREATE DATABASE "{database_name}"')).close()
    try:
        environment = {**os.environ, "DATABASE_URL": test_url}
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "84e008d3ef75"],
            cwd=".",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        migrated = create_engine(test_url)
        with migrated.begin() as connection:
            connection.execute(text("INSERT INTO families(id,name) VALUES ('f','Casa')"))
            connection.execute(text("INSERT INTO users(id,email,name,password_hash,active) VALUES ('d','d@test','Douglas','hash',true),('v','v@test','Vanessa','hash',true)"))
            connection.execute(text("INSERT INTO memberships(family_id,user_id) VALUES ('f','d'),('f','v')"))
            connection.execute(text("INSERT INTO cards(id,family_id,version,created_at,name,institution,holder_id,closing_day,due_day) VALUES ('card','f',1,now(),'Roxo','Nubank','d',25,5)"))
            connection.execute(text("INSERT INTO commitments(id,family_id,version,created_at,description,kind,buyer_id,purchased_at,total_cents,original_count,imported) VALUES ('c','f',1,now(),'Compra','expense','d','2026-09-01',101,1,false)"))
            connection.execute(text("INSERT INTO installments(id,family_id,version,created_at,commitment_id,number,original_cents,amount_cents,original_month,month,original_due,due_date,needs_review,manually_assigned) VALUES ('i','f',1,now(),'c',1,101,101,'2026-09-01','2026-09-01','2026-09-01','2026-09-01',false,false)"))
            connection.execute(text("INSERT INTO responsibility_shares(id,family_id,version,created_at,commitment_id,user_id,weight,position) VALUES ('sd','f',1,now(),'c','d',51,0),('sv','f',1,now(),'c','v',50,1)"))
            connection.execute(
                text(
                    "INSERT INTO recurring_rules(id,family_id,version,created_at,description,start_month,amount_cents,variable,due_day,shares) "
                    "VALUES ('r','f',1,now(),'Conta','2026-09-01',101,false,10,:shares)"
                ),
                {"shares": '[{"user_id":"d","weight":51},{"user_id":"v","weight":50}]'},
            )
            connection.execute(text("INSERT INTO recurring_occurrences(id,family_id,version,created_at,recurrence_id,month,due_date,amount_cents,estimated) VALUES ('o','f',1,now(),'r','2026-09-01','2026-09-10',101,false)"))
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=".",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        with migrated.connect() as connection:
            assert connection.execute(text("SELECT name, role FROM memberships JOIN users ON users.id=user_id ORDER BY name")).all() == [("Douglas", "owner"), ("Vanessa", "member")]
            card = connection.execute(text("SELECT institution_key,institution_name FROM cards WHERE id='card'")).one()
            assert card == ("nubank", "Nubank")
            assert connection.scalar(text("SELECT length(code) FROM families WHERE id='f'")) == 10
            assert connection.execute(text("SELECT user_id,weight,position FROM installment_responsibility_shares ORDER BY position")).all() == [("d", 51, 0), ("v", 50, 1)]
            assert connection.execute(text("SELECT user_id,weight,position FROM occurrence_responsibility_shares ORDER BY position")).all() == [("d", 51, 0), ("v", 50, 1)]
        migrated.dispose()
    finally:
        admin.connect().execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')).close()
        admin.dispose()


def test_populated_upgrade_rejects_ambiguous_owner():
    database_name = f"expense_migration_{uuid4().hex}"
    admin_url = settings.database_url.rsplit("/", 1)[0] + "/postgres"
    test_url = settings.database_url.rsplit("/", 1)[0] + f"/{database_name}"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    try:
        environment = {**os.environ, "DATABASE_URL": test_url}
        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "84e008d3ef75"],
            cwd=".",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        ambiguous = create_engine(test_url)
        with ambiguous.begin() as connection:
            connection.execute(text("INSERT INTO families(id,name) VALUES ('f','Casa')"))
            connection.execute(
                text(
                    "INSERT INTO users(id,email,name,password_hash,active) VALUES "
                    "('a','a@test','Alice','hash',true),('b','b@test','Bruno','hash',true)"
                )
            )
            connection.execute(
                text("INSERT INTO memberships(family_id,user_id) VALUES ('f','a'),('f','b')")
            )
        ambiguous.dispose()
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=".",
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Cannot determine a unique owner for family f" in result.stderr
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        admin.dispose()


def test_rls_denies_foreign_rows(db):
    db.execute(text("INSERT INTO families(id,name,code,version,created_at) VALUES ('a','A','ACODEABCDE',1,now()),('b','B','BCODEABCDE',1,now())"))
    db.execute(
        text(
            "INSERT INTO month_closures(id,family_id,version,created_at,month,closed) VALUES ('ca','a',1,now(),'2026-10-01',true),('cb','b',1,now(),'2026-10-01',true)"
        )
    )
    db.execute(text("SET LOCAL ROLE expense_app"))
    assert db.execute(text("SELECT id FROM month_closures")).all() == []
    db.execute(text("SELECT set_config('app.family_id','a',true)"))
    assert db.execute(text("SELECT id FROM month_closures")).scalars().all() == ["ca"]
    assert (
        db.execute(text("UPDATE month_closures SET closed=false WHERE id='cb' RETURNING id")).all()
        == []
    )


def test_foreign_family_relationship_rejected(db):
    db.execute(text("INSERT INTO families(id,name,code,version,created_at) VALUES ('a','A','ACODEABCDF',1,now()),('b','B','BCODEABCDF',1,now())"))
    db.execute(
        text(
            "INSERT INTO users(id,email,name,password_hash,active,version,created_at) "
            "VALUES ('u','u@test','User','hash',true,1,now())"
        )
    )
    db.execute(
        text(
            "INSERT INTO memberships(family_id,user_id,role,created_at) "
            "VALUES ('a','u','owner',now())"
        )
    )
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO cards(id,family_id,version,created_at,name,institution_name,institution_key,holder_id,closing_day,due_day) VALUES ('c','b',1,now(),'Card','Bank','other','u',25,5)"
            )
        )
