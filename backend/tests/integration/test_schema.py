"""T3 / FAM-01 AC02: persisted isolation, not a mock of authorization."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def test_rls_denies_foreign_rows(db):
    db.execute(text("INSERT INTO families(id,name) VALUES ('a','A'),('b','B')"))
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
    db.execute(text("INSERT INTO families(id,name) VALUES ('a','A'),('b','B')"))
    db.execute(
        text(
            "INSERT INTO users(id,email,name,password_hash,active) VALUES ('u','u@test','User','hash',true)"
        )
    )
    db.execute(text("INSERT INTO memberships VALUES ('a','u')"))
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO cards(id,family_id,version,created_at,name,institution,holder_id,closing_day,due_day) VALUES ('c','b',1,now(),'Card','Bank','u',25,5)"
            )
        )
