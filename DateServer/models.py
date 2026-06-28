from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ParsedDate:
    date_obj: datetime
    iso_format: str
    weekday: str

@dataclass
class DateRange:
    start: datetime
    end: datetime
    description: str