"""EDIT-02 AC2/AC4: reusable commitment schedule calculation."""

from datetime import date

from app.domain.commitments import build_commitment_schedule


def test_cash_schedule_distributes_cents_and_months_without_state():
    result = build_commitment_schedule(
        total_cents=101,
        count=2,
        first_month=date(2026, 10, 1),
    )

    assert [part["amount_cents"] for part in result] == [51, 50]
    assert [part["month"] for part in result] == [date(2026, 10, 1), date(2026, 11, 1)]
    assert [part["due_date"] for part in result] == [date(2026, 10, 1), date(2026, 11, 1)]
    assert [part["number"] for part in result] == [1, 2]


def test_card_schedule_uses_cycle_due_rules_and_review_flag():
    result = build_commitment_schedule(
        total_cents=300,
        count=3,
        first_month=date(2026, 10, 1),
        closing_day=25,
        due_day=5,
        needs_review=True,
    )

    assert [part["due_date"] for part in result] == [
        date(2026, 10, 5),
        date(2026, 11, 5),
        date(2026, 12, 5),
    ]
    assert all(part["needs_review"] is True for part in result)
