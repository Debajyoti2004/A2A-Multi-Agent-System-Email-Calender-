import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def get_last_day_of_month(dt: datetime) -> datetime:
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.replace(day=last_day)

def get_first_day_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1)

def add_business_days(start_date: datetime, days: int) -> datetime:
    current_date = start_date
    added_days = 0
    while added_days < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            added_days += 1
    return current_date