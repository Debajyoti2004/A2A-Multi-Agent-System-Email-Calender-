import os
import re
import calendar
import json
import pickle
import dateparser
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict
from google_auth import get_calendar_service

GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}

def retrieve_timezones() -> Dict[str, str]:
    path = os.getenv("USERS_TIMEZONES_PATH")
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except:
        return {}

def parse_natural_date(natural_str: str, reference_timezone: str = "UTC") -> str:
    natural_str_lower = natural_str.strip().lower()
    today = datetime.now(ZoneInfo(reference_timezone))

    if natural_str_lower == "today":
        return today.date().isoformat()
    if natural_str_lower == "tomorrow":
        return (today + timedelta(days=1)).date().isoformat()

    weekday_match = re.search(r"(this|next)?\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", natural_str_lower)
    if weekday_match:
        when, weekday_str = weekday_match.groups()
        target_weekday = WEEKDAYS[weekday_str]
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday + 7) % 7
        if when == "next": days_ahead += 7
        elif when is None and days_ahead == 0: days_ahead = 7
        return (today + timedelta(days=days_ahead)).date().isoformat()

    parsed_dt = dateparser.parse(
        natural_str,
        languages=['en'],
        settings={'TIMEZONE': reference_timezone, 'RETURN_AS_TIMEZONE_AWARE': True, 'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': today}
    )
    if not parsed_dt:
        raise ValueError(f"Unable to parse date: {natural_str}")
    return parsed_dt.date().isoformat()

def find_unique_event(service, event_name: str, event_date: Optional[str] = None):
    now_utc = datetime.now(ZoneInfo("UTC"))
    if event_date:
        event_date_iso = parse_natural_date(event_date)
        time_min = datetime.fromisoformat(f"{event_date_iso}T00:00:00").replace(tzinfo=ZoneInfo("UTC"))
        time_max = datetime.fromisoformat(f"{event_date_iso}T23:59:59").replace(tzinfo=ZoneInfo("UTC"))
    else:
        time_min = now_utc
        time_max = now_utc + timedelta(days=365)

    events_result = service.events().list(
        calendarId=GOOGLE_CALENDAR_ID,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        q=event_name,
        singleEvents=True
    ).execute()
    events = events_result.get('items', [])

    if not events: return None, "No event found."
    if len(events) > 1: return None, "Multiple events found. Be more specific."
    return events[0], None