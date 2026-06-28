import os
import pickle
from datetime import datetime
from zoneinfo import ZoneInfo
from mcp.server.fastmcp import FastMCP
from calendar_logic import retrieve_timezones

mcp = FastMCP("config_server")

@mcp.tool(description="""
Persistently stores the preferred home timezone for a specific user. 
Requires a 'user_id' and a valid IANA timezone string (e.g., 'America/New_York', 'Asia/Kolkata'). 
Use this tool when a user explicitly states their location or requests to change their 
default time settings for calendar and scheduling operations.
""")
def set_user_home_timezone(user_id: str, timezone: str) -> str:
    user_timezones = retrieve_timezones()
    try:
        ZoneInfo(timezone)
        user_timezones[user_id] = timezone
        with open(os.getenv("USERS_TIMEZONES_PATH"), "wb") as f:
            pickle.dump(user_timezones, f)
        return f"Success. Timezone set to {timezone}."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool(description="""
Retrieves the stored home timezone for a specific user ID. 
Always call this tool before performing any calendar checks, meeting creations, or 
availability lookups to ensure that the time math is adjusted correctly to the user's 
local context. Returns 'Timezone not found' if no preference has been set yet.
""")
def retrieve_user_timezone(user_id: str) -> str:
    user_timezones = retrieve_timezones()
    return user_timezones.get(user_id, "Timezone not found.")

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from dotenv import load_dotenv
    import sys

    load_dotenv()
    console = Console(stderr=True)

    console.print(Panel(
        Align.center("[bold green]MCP Configuration Server[/bold green]\n[white]Preference & Timezone Management[/white]"),
        border_style="green",
        title="[bold green]System Boot[/bold green]"
    ))

    # try:
    #     with console.status("[bold yellow]Running pre-flight checks...") as status:
    #         current_date = get_todays_date()
            
    #         storage_path = os.getenv("USERS_TIMEZONES_PATH", "timezones.pkl")
            
    #         test_id = "system_test_user"
    #         test_zone = "UTC"
    #         set_status = set_user_home_timezone(test_id, test_zone)
    #         fetched_zone = retrieve_user_timezone(test_id)

    #     table = Table(show_header=True, header_style="bold green", expand=True)
    #     table.add_column("Component", style="dim")
    #     table.add_column("Result")
    #     table.add_column("Status", justify="center")

    #     table.add_row("System Clock", current_date, "[green]ACTIVE[/green]")
    #     table.add_row("Persistence Layer", storage_path, "[green]CONNECTED[/green]")
    #     table.add_row("Write Permission", set_status, "[green]SUCCESS[/green]")
    #     table.add_row("Read Permission", fetched_zone, "[green]VERIFIED[/green]")

    #     console.print(table)
    #     console.print("\n[bold green]●[/bold green] [white]Config engine operational. Switching to Stdio Transport.[/white]\n")

    # except Exception as e:
    #     console.print(Panel(
    #         f"[bold red]System Initialization Failed[/bold red]\n[white]{str(e)}[/white]",
    #         title="[red]BOOT_ERROR[/red]",
    #         border_style="red"
    #     ))
    #     sys.exit(1)

    mcp.run(transport="stdio")  