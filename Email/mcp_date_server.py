import json
from mcp.server.fastmcp import FastMCP
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import os 
import sys 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from DateServer import TemporalParser, DATE_FORMAT

mcp = FastMCP("temporal_engine")
engine = TemporalParser()

def print_startup_panel():
    console = Console(stderr=True)
    startup_message = Align.center(
        "[bold green]MCP Date Server Start[/bold green]\n"
        "[white]Temporal Reasoning Engine is now online[/white]"
    )
    panel = Panel(
        startup_message,
        title="[bold blue]System Status[/bold blue]",
        border_style="cyan",
        padding=(1, 2),
        subtitle="[dim]Ready for Stdio Transport[/dim]"
    )
    
    console.print(panel)

@mcp.tool(description="""
    Production-grade temporal reasoning tool. 
    Converts complex natural language (relative, weekdays, business logic) 
    into standard YYYY/MM/DD format.
    """)
def parse_natural_date(query: str) -> str:
    try:
        result = engine.parse(query)
        if result:
            return result.strftime(DATE_FORMAT)
        return json.dumps({"error": "Unresolvable temporal expression"})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # import datetime
    # print(f"--- Temporal Engine Logic Test ---")
    # print(f"Reference Time: {datetime.datetime.now().strftime('%Y/%m/%d %A')}\n")

    # test_queries = [
    #     "today",
    #     "yesterday",
    #     "day before yesterday",
    #     "last monday",
    #     "next friday",
    #     "3 weeks ago",
    #     "15 days from now",
    #     "end of this month",
    #     "start of next month",
    #     "end of next month"
    # ]

    # for q in test_queries:
    #     res = parse_natural_date(q)
    #     print(f"Input: {q:25} -> Output: {res}")

    # print(f"\nLogic test complete. Starting MCP Server...\n")
    print_startup_panel()
    mcp.run(transport="stdio")