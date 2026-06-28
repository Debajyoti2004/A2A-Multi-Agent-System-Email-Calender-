import os
import re
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from mcp.server.fastmcp import FastMCP
from google_auth import get_calendar_service
from calendar_logic import parse_natural_date, find_unique_event, GOOGLE_CALENDAR_ID

mcp = FastMCP("calendar_server")

@mcp.tool(description="""
Checks the user's Google Calendar for available time slots within a specific window. 
Arguments: 
- search_date: Natural language date (e.g., 'tomorrow', 'next Monday').
- start_time: Start of search window (e.g., '09:00AM').
- end_time: End of search window (e.g., '05:00PM').
- duration_minutes: Expected meeting length.
- timezone: User's IANA timezone.
If the requested slot is busy, the tool automatically scans the next 7 days and returns the next available alternative.
""")
def check_availability(search_date: str, start_time: str, end_time: str, duration_minutes: int, timezone: str) -> str:
    start_time, end_time = start_time.replace(" ", ""), end_time.replace(" ", "")
    try:
        date_iso = parse_natural_date(search_date, timezone)
        search_tz, utc_tz = ZoneInfo(timezone), ZoneInfo("UTC")
        
        start_dt = datetime.combine(datetime.fromisoformat(date_iso).date(), datetime.strptime(start_time, '%I:%M%p').time()).replace(tzinfo=search_tz)
        end_dt = datetime.combine(datetime.fromisoformat(date_iso).date(), datetime.strptime(end_time, '%I:%M%p').time()).replace(tzinfo=search_tz)
        
        service = get_calendar_service()
        events_result = service.events().list(calendarId=GOOGLE_CALENDAR_ID, timeMin=start_dt.astimezone(utc_tz).isoformat(), timeMax=end_dt.astimezone(utc_tz).isoformat(), singleEvents=True, orderBy='startTime').execute()
        busy_slots = events_result.get('items', [])
        
        if not busy_slots:
            return json.dumps({
                "status": "AVAILABLE",
                "message": f"The slot on {search_date} between {start_time} and {end_time} is open.",
                "requested_window": {"start": start_time, "end": end_time}
            })
        
        conflicting_events = [e.get('summary', 'Untitled') for e in busy_slots]
        meeting_duration = timedelta(minutes=duration_minutes)
        
        for i in range(1, 8):
            next_day = start_dt + timedelta(days=i)
            win_start = next_day.replace(hour=9, minute=0, second=0).astimezone(utc_tz)
            win_end = next_day.replace(hour=17, minute=0, second=0).astimezone(utc_tz)
            
            fb_events = service.events().list(calendarId=GOOGLE_CALENDAR_ID, timeMin=win_start.isoformat(), timeMax=win_end.isoformat(), singleEvents=True, orderBy='startTime').execute().get('items', [])
            
            curr = win_start
            for event in fb_events:
                ev_start = datetime.fromisoformat(event['start'].get('dateTime'))
                if curr + meeting_duration <= ev_start:
                    return json.dumps({
                        "status": "BUSY",
                        "conflicts": conflicting_events,
                        "suggestion": f"{curr.astimezone(search_tz).strftime('%A, %B %d at %I:%M %p')}"
                    })
                curr = max(curr, datetime.fromisoformat(event['end'].get('dateTime')))
            
            if curr + meeting_duration <= win_end:
                return json.dumps({
                    "status": "BUSY",
                    "conflicts": conflicting_events,
                    "suggestion": f"{curr.astimezone(search_tz).strftime('%A, %B %d at %I:%M %p')}"
                })
            
        return json.dumps({"status": "BUSY", "message": "No availability found in the next 7 days."})
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

@mcp.tool(description="""
Creates a new event on the user's Google Calendar. 
Arguments:
- title: The summary/name of the meeting.
- start_time_str: The time in natural language or ISO format (e.g., 'Friday at 2pm').
- duration_minutes: Integer length of the meeting.
- event_timezone: IANA timezone string.
Returns a confirmation message with the HTML link to the created event.
""")
def create_meeting(title: str, start_time_str: str, duration_minutes: int, event_timezone: str) -> str:
    try:
        service = get_calendar_service()
        date_iso = parse_natural_date(start_time_str, event_timezone)
        time_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b', start_time_str, re.IGNORECASE)
        time_obj = datetime.strptime(time_match.group(1).replace(" ", "").upper(), '%I:%M%p' if ':' in time_match.group(1) else '%I%p').time()
        
        start_dt = datetime.combine(datetime.fromisoformat(date_iso).date(), time_obj).replace(tzinfo=ZoneInfo(event_timezone))
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': title,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': event_timezone},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': event_timezone}
        }
        res = service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        
        return json.dumps({
            "status": "SUCCESS",
            "event_details": {
                "title": title,
                "scheduled_time": start_dt.strftime('%A, %B %d at %I:%M %p'),
                "link": res.get('htmlLink')
            }
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

@mcp.tool(description="""
Removes an existing event from the Google Calendar by name.
Arguments:
- event_name: The exact or partial title of the event.
- event_date: (Optional) Natural language date to narrow down the search if multiple events have similar names.
Returns a success message or an error if the event is not found or ambiguous.
""")
def delete_calendar_event(event_name: str, event_date: str = None) -> str:
    try:
        service = get_calendar_service()
        event, err = find_unique_event(service, event_name, event_date)
        if err:
            return json.dumps({"status": "ERROR", "message": err})
        
        service.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=event['id']).execute()
        return json.dumps({
            "status": "SUCCESS",
            "message": f"Successfully deleted event: {event.get('summary')}",
            "deleted_time": event['start'].get('dateTime')
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from rich import box
    from dotenv import load_dotenv
    import sys
    import json

    load_dotenv()
    console = Console(stderr=True)

    console.print(Panel(
        Align.center("[bold yellow]MCP Google Calendar Engine[/bold yellow]\n[white]Operational Logic Verification[/white]"),
        border_style="yellow",
        title="[bold white]Boot Sequence[/bold white]"
    ))

    # try:
    #     with console.status("[bold yellow]Running Diagnostic Suite...") as status:
    #         test_tz = "UTC"
    #         unique_test_title = f"AI_TEST_{int(datetime.now().timestamp())}"
            
    #         avail_res = check_availability(
    #             search_date="next Monday",
    #             start_time="10:00AM",
    #             end_time="11:00AM",
    #             duration_minutes=30,
    #             timezone=test_tz
    #         )
    #         avail_data = json.loads(avail_res)

    #         create_res = create_meeting(
    #             title=unique_test_title,
    #             start_time_str="tomorrow at 2:30pm",
    #             duration_minutes=15,
    #             event_timezone=test_tz
    #         )
    #         create_data = json.loads(create_res)

    #         delete_res = delete_calendar_event(
    #             event_name=unique_test_title,
    #             event_date="tomorrow"
    #         )
    #         delete_data = json.loads(delete_res)

    #     table = Table(title="[bold magenta]Tool diagnostic Report[/bold magenta]", expand=True, box=box.DOUBLE_EDGE)
    #     table.add_column("Tool", style="cyan")
    #     table.add_column("Test Query", style="white")
    #     table.add_column("Status", justify="center")
        
    #     table.add_row("check_availability", "next Monday 10am-11am", f"[{avail_data.get('status')}]")
    #     table.add_row("create_meeting", unique_test_title, f"[{create_data.get('status')}]")
    #     table.add_row("delete_calendar_event", unique_test_title, f"[{delete_data.get('status')}]")
    #     console.print(table)

    #     console.print(Panel(
    #         f"[bold blue]Availability Result:[/bold blue] {avail_data.get('message', 'Suggestion: ' + avail_data.get('suggestion', 'None'))}",
    #         border_style="blue"
    #     ))

    #     console.print(Panel(
    #         f"[bold green]Creation Result:[/bold green] {create_data.get('event_details', {}).get('scheduled_time')}\n[dim]Link: {create_data.get('event_details', {}).get('link')}[/dim]",
    #         border_style="green"
    #     ))

    #     console.print(Panel(
    #         f"[bold red]Cleanup Result:[/bold red] {delete_data.get('message')}",
    #         border_style="red"
    #     ))

    #     console.print("\n[bold green]✔[/bold green] [white]Bridge verified. Initializing Stdio Transport.[/white]\n")

    # except Exception as e:
    #     console.print(Panel(f"[bold red]Diagnostic Failed[/bold red]\n{str(e)}", border_style="red"))
    #     sys.exit(1)

    mcp.run(transport="stdio")