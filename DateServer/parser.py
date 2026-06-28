import dateparser
import parsedatetime
from datetime import datetime
from DateServer.resolver import Dispatcher
from .config import TIMEZONE

class TemporalParser:
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.cal = parsedatetime.Calendar()

    def parse(self, query: str) -> datetime:
        now = datetime.now(TIMEZONE).replace(tzinfo=None)
        
        resolved = self.dispatcher.dispatch(query, now)
        if resolved: return resolved

        time_struct, status = self.cal.parse(query, sourceTime=now)
        if status > 0:
            return datetime(*time_struct[:6])

        parsed = dateparser.parse(query, settings={'RELATIVE_BASE': now, 'PREFER_DATES_FROM': 'past'})
        return parsed