from datetime import datetime
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

class WeekdayResolver:
    def resolve(self, query: str, now: datetime) -> datetime:
        q = query.lower()
        mapping = {"monday": MO, "tuesday": TU, "wednesday": WE, "thursday": TH, "friday": FR, "saturday": SA, "sunday": SU}
        
        for day_name, day_code in mapping.items():
            if day_name in q:
                if "last" in q: return now + relativedelta(weekday=day_code(-1))
                if "next" in q: return now + relativedelta(weekday=day_code(+1))
                if "this" in q: return now + relativedelta(weekday=day_code(0))
        return None