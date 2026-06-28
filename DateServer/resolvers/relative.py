import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class RelativeResolver:
    def resolve(self, query: str, now: datetime) -> datetime:
        q = query.lower()
        if q == "today": return now
        if q == "tomorrow": return now + timedelta(days=1)
        if q == "yesterday": return now - timedelta(days=1)
        if q == "day before yesterday": return now - timedelta(days=2)
        if q == "day after tomorrow": return now + timedelta(days=2)
        
        match = re.search(r"(\d+)\s+(day|week|month|year)s?\s+(ago|later|from now)", q)
        if match:
            val, unit, direction = int(match.group(1)), match.group(2), match.group(3)
            mult = -1 if direction == "ago" else 1
            if unit == "day": return now + timedelta(days=val * mult)
            if unit == "week": return now + timedelta(weeks=val * mult)
            if unit == "month": return now + relativedelta(months=val * mult)
            if unit == "year": return now + relativedelta(years=val * mult)
        return None