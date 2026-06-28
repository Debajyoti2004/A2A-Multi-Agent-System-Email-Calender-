from DateServer.resolvers import RelativeResolver, WeekdayResolver, MonthResolver
import datetime

class Dispatcher:
    def __init__(self):
        self.resolvers = [
            RelativeResolver(),
            WeekdayResolver(),
            MonthResolver()
        ]

    def dispatch(self, query: str, now: datetime):
        for resolver in self.resolvers:
            result = resolver.resolve(query, now)
            if result:
                return result
        return None