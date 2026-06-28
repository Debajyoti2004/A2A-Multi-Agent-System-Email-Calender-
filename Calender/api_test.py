import os
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

def discover_models():
    load_dotenv()
    console = Console()
    
    # 1. Setup Header
    console.print(Panel.fit(
        "[bold cyan]Gemini API Discovery Engine[/bold cyan]\n"
        "[dim]Scanning authorized models for your specific API Key[/dim]",
        border_style="cyan"
    ))

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[bold red]❌ ERROR:[/bold red] GOOGLE_API_KEY not found in .env")
        return

    genai.configure(api_key=api_key)

    # 2. Loading State
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Contacting Google Model Service...", total=None)
        try:
            available_models = list(genai.list_models())
        except Exception as e:
            console.print(f"[bold red]Critical API Error:[/bold red] {e}")
            return

    # 3. Build the Results Table
    table = Table(
        title="[bold white]Authorized Generative Models[/bold white]",
        show_header=True, 
        header_style="bold magenta",
        expand=True
    )
    
    table.add_column("Display Name", style="yellow")
    table.add_column("Technical Model ID (Use this in code)", style="bold green")
    table.add_column("Input Limit", justify="right", style="cyan")
    table.add_column("Output Limit", justify="right", style="blue")

    count = 0
    for m in available_models:
        # We only care about models that support generation
        if 'generateContent' in m.supported_generation_methods:
            table.add_row(
                m.display_name,
                m.name.replace("models/", ""), # This is the string you need for agents.py
                f"{m.input_token_limit:,}",
                f"{m.output_token_limit:,}"
            )
            count += 1

    # 4. Final Display
    if count > 0:
        console.print(table)
        console.print(f"\n[bold green]✔ Found {count} usable models.[/bold green]")
        console.print("[dim]Note: If a model isn't listed here, your key doesn't have permission to use it yet.[/dim]\n")
    else:
        console.print("[bold red]No generation models found for this API key.[/bold red]")

if __name__ == "__main__":
    discover_models()