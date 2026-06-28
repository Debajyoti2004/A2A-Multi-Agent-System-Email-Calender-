import os
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "UTC"))
COUNTRY_CODE = os.getenv("COUNTRY_CODE", "US")
DATE_FORMAT = "%Y/%m/%d"
DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"