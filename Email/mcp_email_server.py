import os
import json
import base64
from email.mime.text import MIMEText
from mcp.server.fastmcp import FastMCP
from gmail_auth import get_gmail_service

mcp = FastMCP("email_server")

def parse_message(msg):
    payload = msg.get('payload', {})
    headers = payload.get('headers', [])
    
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown")
    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), "Unknown")
    
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    return {
        "uid": msg['id'],
        "subject": subject,
        "from": sender,
        "date": date,
        "content": body[:1200].strip()
    }

@mcp.tool(description="""
Fetches emails using structured filters via Gmail API. 
Args: sender, subject, date (YYYY/MM/DD), unread_only (bool), limit (int).
""")
def email_fetch_tool(sender: str = None, subject: str = None, date: str = None, unread_only: bool = False, limit: int = 10) -> str:
    try:
        service = get_gmail_service()
        query_parts = []
        if unread_only: query_parts.append("is:unread")
        if sender: query_parts.append(f"from:{sender}")
        if subject: query_parts.append(f"subject:{subject}")
        if date: query_parts.append(f"after:{date}")
        
        q = " ".join(query_parts) if query_parts else "label:INBOX"
        
        results = service.users().messages().list(userId='me', q=q, maxResults=limit).execute()
        messages = results.get('messages', [])
        
        output = []
        for m in messages:
            full_msg = service.users().messages().get(userId='me', id=m['id']).execute()
            output.append(parse_message(full_msg))
            
        return json.dumps(output)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool(description="Advanced Gmail API search using native operators like 'has:attachment' or 'is:important'.")
def smart_search_tool(gmail_query: str) -> str:
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', q=gmail_query, maxResults=10).execute()
        messages = results.get('messages', [])
        
        output = []
        for m in messages:
            full_msg = service.users().messages().get(userId='me', id=m['id']).execute()
            output.append(parse_message(full_msg))
            
        return json.dumps(output)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool(description="Dispatches an outbound email via Gmail API.")
def send_email_tool(to: str, subject: str, body: str) -> str:
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_msg = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        
        return json.dumps({
            "status": "sent", 
            "id": sent_msg['id'],
            "recipient": to,
            "subject": subject
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from rich import box
    from dotenv import load_dotenv
    import sys

    load_dotenv()
    console = Console(stderr=True)

    console.print(Panel(
        Align.center("[bold cyan]MCP Gmail API Engine[/bold cyan]\n[white]OAuth2 Control Plane Initialized[/white]"),
        border_style="blue",
        title="[bold blue]Boot Sequence[/bold blue]"
    ))

    # try:
    #     with console.status("[bold yellow]Running pre-flight diagnostics...") as status:
    #         service = get_gmail_service()
    #         user_profile = service.users().getProfile(userId='me').execute()
            
    #         # --- FILTER TESTING SECTION ---
    #         # Uncomment the specific filter you want to test:

    #         # 1. Default (No filters, just limit)
    #         # raw_emails = email_fetch_tool(limit=5)

    #         # 2. Test Subject Filter
    #         # raw_emails = email_fetch_tool(subject="LinkedIn", limit=5)

    #         # 3. Test Date Filter (Format: YYYY/MM/DD)
    #         raw_emails = email_fetch_tool(date="2026/06/20", limit=5)

    #         # 4. Test Both (Subject and Date)
    #         # raw_emails = email_fetch_tool(subject="AI", date="2026/06/01", limit=5)
            
    #         # ------------------------------
            
    #         emails_list = json.loads(raw_emails)

    #     status_table = Table(show_header=True, header_style="bold magenta", expand=True, box=box.ROUNDED)
    #     status_table.add_column("Account", style="cyan")
    #     status_table.add_column("Status", justify="center")
    #     status_table.add_column("Total Messages", justify="right")
        
    #     status_table.add_row(
    #         user_profile['emailAddress'], 
    #         "[bold green]AUTHORIZED[/bold green]", 
    #         str(user_profile['messagesTotal'])
    #     )
    #     console.print(status_table)

    #     # Added a check to ensure we handle empty results gracefully if the filter is too strict
    #     if isinstance(emails_list, list) and len(emails_list) > 0:
    #         email_table = Table(
    #             title="[bold cyan]Latest Gmail API Data Retrieval[/bold cyan]",
    #             expand=True,
    #             box=box.SIMPLE_HEAVY,
    #             header_style="bold white on blue"
    #         )
    #         email_table.add_column("ID", style="dim")
    #         email_table.add_column("From", style="green")
    #         email_table.add_column("Subject", style="bold white", ratio=3)
    #         email_table.add_column("Content Preview", style="italic dim", ratio=2)

    #         for mail in emails_list:
    #             email_table.add_row(
    #                 str(mail.get("uid")[:8]),
    #                 str(mail.get("from")).split("<")[0][:20],
    #                 str(mail.get("subject"))[:40],
    #                 str(mail.get("content"))[:50].replace("\n", " ") + "..."
    #             )
    #         console.print(email_table)
    #     else:
    #         console.print("[yellow]No emails found matching your filter criteria.[/yellow]")

    #     console.print("\n[bold green]●[/bold green] [white]Bridge verified. Initializing Stdio Transport.[/white]\n")
    # except Exception as e:
    #     console.print(Panel(f"[bold red]Initialization Failed[/bold red]\n{str(e)}", border_style="red"))
    #     sys.exit(1)

    mcp.run(transport="stdio")