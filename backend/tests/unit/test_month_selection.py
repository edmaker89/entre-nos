"""MONTH-01 AC01/08."""

from datetime import datetime, timezone
from app.domain.month_selection import default_month


def test_day_ten_and_explicit_closure():
    assert default_month(datetime(2026, 10, 9, 12, tzinfo=timezone.utc), False) == "2026-10"
    assert default_month(datetime(2026, 10, 10, 12, tzinfo=timezone.utc), False) == "2026-11"
    assert default_month(datetime(2026, 10, 5, 12, tzinfo=timezone.utc), True) == "2026-11"
    assert default_month(datetime(2026, 11, 1, 12, tzinfo=timezone.utc), False) == "2026-11"
    assert default_month(datetime(2026, 10, 10, 1, tzinfo=timezone.utc), False) == "2026-10"
    assert default_month(datetime(2026, 12, 10, 12, tzinfo=timezone.utc), False) == "2027-01"
