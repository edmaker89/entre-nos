from calendar import monthrange
from datetime import date


def month_start(value: date) -> date:
    return value.replace(day=1)


def add_months(value: date, count: int) -> date:
    index = value.year * 12 + value.month - 1 + count
    year, month = divmod(index, 12)
    return date(year, month + 1, min(value.day, monthrange(year, month + 1)[1]))


def on_day(month: date, day: int) -> date:
    return date(month.year, month.month, min(day, monthrange(month.year, month.month)[1]))


def cycle_for_month(month: date, closing_day: int, due_day: int) -> dict:
    month = month_start(month)
    due = on_day(month, due_day)
    closing = on_day(month, closing_day)
    if closing >= due:
        closing = on_day(add_months(month, -1), closing_day)
    return {"month": month, "closing_date": closing, "due_date": due}


def first_cycle(purchased_at: date, closing_day: int, due_day: int) -> dict:
    for offset in range(3):
        cycle = cycle_for_month(add_months(month_start(purchased_at), offset), closing_day, due_day)
        if purchased_at <= cycle["closing_date"]:
            return {**cycle, "needs_review": purchased_at == cycle["closing_date"]}
    raise ValueError("Ciclo inválido.")
