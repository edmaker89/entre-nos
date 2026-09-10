"""CARD-01 AC01–03; BUY-01 AC01–03."""

from datetime import date
import pytest
from app.domain.cycles import first_cycle, cycle_for_month, add_months, month_start


@pytest.mark.parametrize(
    "day,month,review",
    [(24, date(2026, 10, 1), False), (25, date(2026, 10, 1), True), (26, date(2026, 11, 1), False)],
)
def test_closing_boundary(day, month, review):
    cycle = first_cycle(date(2026, 9, day), 25, 5)
    assert cycle["month"] == month
    assert cycle["needs_review"] == review
    assert cycle["due_date"] == date(month.year, month.month, 5)


def test_last_day_clamping_and_year_rollover():
    cycle = cycle_for_month(date(2027, 3, 1), 31, 5)
    assert cycle["closing_date"] == date(2027, 2, 28)
    assert cycle["due_date"] == date(2027, 3, 5)
    assert add_months(date(2026, 12, 1), 1) == date(2027, 1, 1)
    assert month_start(date(2026, 10, 15)) == date(2026, 10, 1)


def test_equal_closing_due_days_means_following_month():
    cycle = first_cycle(date(2026, 9, 5), 5, 5)
    assert cycle["closing_date"] == date(2026, 9, 5)
    assert cycle["due_date"] == date(2026, 10, 5)
