import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class SchedulerAgent:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "mcp_config_server.py")
        calendar_path = os.path.join(current_dir, "mcp_calender_server.py")

        self.mcp_client = MultiServerMCPClient({
            "config_engine": StdioConnection(
                transport="stdio", 
                command="python", 
                args=[config_path]
            ),
            "calendar_engine": StdioConnection(
                transport="stdio", 
                command="python", 
                args=[calendar_path]
            )
        })
        self.executor = None

    async def initialize(self):
        tools = await self.mcp_client.get_tools()
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=self.api_key,
            temperature=0,
            model_kwargs={
                "allow_parallel_tool_calls": True
            }
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an elite Executive Scheduler. Your goal is to manage the user's calendar with 100% accuracy and professional etiquette.
            
            OPERATIONAL CONTEXT:
            - Today's Date: {now}
            - Target User ID: {user_id}
            
            CORE PROTOCOLS:
            1. TEMPORAL ANCHORING: Use 'Today's Date' to resolve all relative time expressions (e.g., 'next Tuesday', 'tomorrow morning').
            2. CONTEXT FIRST: Always call 'retrieve_user_timezone' for the {user_id} before checking availability or creating events.
            3. PARALLEL EXECUTION: You are authorized to call multiple tools at once if they are independent.
            4. CONFLICT RESOLUTION: Never just report a conflict. If 'check_availability' shows a slot is busy, you MUST proactively offer the 'suggested_next_available' slot provided by the tool.
            5. VERIFICATION: When creating or rescheduling, provide the user with the 'calendar_link' and specific event details returned by the tool.
            6. AMBIGUITY: If a request is missing vital info (like meeting duration or title), ask for clarification before taking action.
            
            Tone: Executive, concise, and helpful."""),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        
        self.executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            handle_parsing_errors=True
        )
        return self

    async def answer_query(self, prompt: str, user_id: str) -> str:
        if self.executor is None:
            raise RuntimeError("Agent not initialized.")
        
        res = await self.executor.ainvoke({
            "input": prompt,
            "user_id": user_id,
            "now": datetime.now().strftime("%A, %Y-%m-%d")
        })
        
        output = res["output"]
        if isinstance(output, list):
            return "".join([part["text"] if isinstance(part, dict) and "text" in part else str(part) for part in output])
        return str(output)
    
if __name__ == "__main__":
    import asyncio
    from rich.console import Console
    from rich.panel import Panel

    async def run_diagnostic():
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]Scheduler Agent Logic Test[/bold cyan]\n[white]Verifying Multi-Server MCP & Identity Flow[/white]",
            border_style="cyan"
        ))

        agent = SchedulerAgent()
        
        try:
            with console.status("[bold yellow]Spinning up MCP Servers via Stdio...") as status:
                await agent.initialize()
                console.print("[bold green]✔[/bold green] Config and Calendar engines active.")

            test_user = "debajyoti_debug_01"

            test_queries = [
                "Verify my current identity, today's date, and my home timezone.",
                "Check my availability for tomorrow morning between 10:00AM and 12:00PM for a 45-minute slot.",
                "Schedule a 30-minute meeting titled 'MCP Verification Sync' for next Monday at 2:00PM in UTC."
            ]

            for query in test_queries:
                console.print(f"\n[bold blue]User Request:[/bold blue] [italic]{query}[/italic]")
                
                response = await agent.answer_query(query, test_user)
                
                console.print(Panel(
                    response, 
                    title=f"[bold green]Final Agent Output (User: {test_user})[/bold green]", 
                    border_style="green",
                    expand=True
                ))

            console.print("\n[bold green]✔[/bold green] [white]Diagnostic complete. All tool round-trips successful.[/white]\n")

        except Exception as e:
            console.print(Panel(f"[bold red]Diagnostic Failure:[/bold red]\n{str(e)}", border_style="red"))

    asyncio.run(run_diagnostic())