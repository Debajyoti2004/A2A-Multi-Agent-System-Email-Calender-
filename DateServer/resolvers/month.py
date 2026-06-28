from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

class MonthResolver:
    def resolve(self, query: str, now: datetime) -> datetime:
        q = query.lower()
        if "end of this month" in q:
            last_day = calendar.monthrange(now.year, now.month)[1]
            return now.replace(day=last_day)
        if "start of next month" in q:
            return (now + relativedelta(months=1)).replace(day=1)
        if "end of next month" in q:
            target = now + relativedelta(months=1)
            last_day = calendar.monthrange(target.year, target.month)[1]
            return target.replace(day=last_day)
        return None