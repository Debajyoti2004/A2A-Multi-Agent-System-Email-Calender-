import os
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def check_gemini_status():
    load_dotenv()
    console = Console()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        console.print("[bold red]Error: GOOGLE_API_KEY not found in .env file.[/bold red]")
        return

    genai.configure(api_key=api_key)

    console.print(Panel.fit(
        "[bold cyan]Google AI Studio Status[/bold cyan]\n[white]Checking Model Availability & Free Tier Info[/white]",
        border_style="cyan"
    ))

    try:
        # 1. List Available Models
        table = Table(title="Available Models for your API Key", show_header=True, header_style="bold magenta")
        table.add_column("Model Name", style="yellow")
        table.add_column("Version", justify="center")
        table.add_column("Capabilities", style="dim")

        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                table.add_row(
                    m.name.replace('models/', ''), 
                    m.version, 
                    ", ".join(m.supported_generation_methods[:2])
                )
        
        console.print(table)

        # 2. Display Free Tier Knowledge Base
        # These are the standard limits for the "Free Tier" in Google AI Studio
        limit_panel = Panel(
            "[bold green]Gemini 1.5 Flash (Free Tier Limits):[/bold green]\n"
            "• Rate Limit: [bold white]15 RPM[/bold white] (Requests Per Minute)\n"
            "• Daily Limit: [bold white]1,500 RPD[/bold white] (Requests Per Day)\n"
            "• Token Limit: [bold white]1 Million TPM[/bold white] (Tokens Per Minute)\n\n"
            "[bold blue]Gemini 1.5 Pro (Free Tier Limits):[/bold blue]\n"
            "• Rate Limit: [bold white]2 RPM[/bold white] (Requests Per Minute)\n"
            "• Daily Limit: [bold white]50 RPD[/bold white] (Requests Per Day)\n"
            "• Token Limit: [bold white]32,000 TPM[/bold white] (Tokens Per Minute)\n\n"
            "[dim]*Note: Data used in the Free Tier may be used by Google to improve their models.[/dim]",
            title="[bold white]Current Quota Policy[/bold white]",
            border_style="green"
        )
        console.print(limit_panel)

    except Exception as e:
        console.print(f"[bold red]Failed to fetch models:[/bold red] {str(e)}")

if __name__ == "__main__":
    check_gemini_status()