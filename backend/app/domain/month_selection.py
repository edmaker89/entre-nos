from datetime import datetime
from zoneinfo import ZoneInfo
from app.domain.cycles import add_months, month_start


def default_month(time: datetime, closed: bool) -> str:
    local = time.astimezone(ZoneInfo("America/Sao_Paulo")).date()
    month = month_start(local)
    if local.day >= 10 or closed:
        month = add_months(month, 1)
    return month.strftime("%Y-%m")
