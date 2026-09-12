from datetime import date

from app.domain.cycles import add_months, cycle_for_month, month_start
from app.domain.money import installments


def build_commitment_schedule(
    *,
    total_cents: int,
    count: int,
    first_month: date,
    closing_day: int | None = None,
    due_day: int | None = None,
    needs_review: bool = False,
) -> list[dict]:
    """Calculate a purchase schedule without reading or mutating persistence."""
    start = month_start(first_month)
    if (closing_day is None) != (due_day is None):
        raise ValueError("Fechamento e vencimento devem ser informados juntos.")
    result = []
    for index, amount in enumerate(installments(total_cents, count)):
        month = add_months(start, index)
        due = (
            cycle_for_month(month, closing_day, due_day)["due_date"]
            if closing_day is not None and due_day is not None
            else month
        )
        result.append(
            {
                "number": index + 1,
                "amount_cents": amount,
                "month": month,
                "due_date": due,
                "needs_review": needs_review,
            }
        )
    return result
