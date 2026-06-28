import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class EmailAssistantAgent:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        email_server_path = os.path.join(current_dir, "mcp_email_server.py")
        date_server_path = os.path.join(current_dir, "mcp_date_server.py")

        self.mcp_client = MultiServerMCPClient({
            "email_engine": StdioConnection(
                transport="stdio", 
                command="python", 
                args=[email_server_path]
            ),
            "date_engine": StdioConnection(
                transport="stdio", 
                command="python", 
                args=[date_server_path]
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
            ("system", """You are a Senior AI Chief of Staff. Today's Date is {now}.
             
             PROTOCOL:
             1. DATE RESOLUTION: If the user uses relative terms (last Monday, yesterday), use 'parse_natural_date' first.
             2. FETCH PREFERENCE: When a specific date, sender, or subject is known, ALWAYS prefer 'email_fetch_tool'. 
                - Use the 'unread_only' argument if the user asks for new/unread mail.
                - Pass the resolved YYYY/MM/DD date to the 'date' parameter.
             3. SMART SEARCH: Use 'smart_search_tool' ONLY for non-standard queries like 'has:attachment' or 'larger:10mb'.
             4. FALLBACK: If a tool returns an error or empty list, do not repeat the same failed query. Try a broader search or inform the user.
             5. DISPATCH: Before sending, ensure the tone matches thread history (Professional/Technical/Social). Present the final JSON receipt to the user.
             
             Parallel execution is encouraged for complex multi-part requests."""),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        
        self.executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=10
        )
        return self

    async def answer_query(self, prompt: str) -> str:
        if self.executor is None:
            raise RuntimeError("Agent not initialized.")
        
        res = await self.executor.ainvoke({
            "input": prompt,
            "now": datetime.now().strftime("%A, %Y/%m/%d")
        })
        
        output = res["output"]
        if isinstance(output, list):
            return "".join([part["text"] if isinstance(part, dict) and "text" in part else str(part) for part in output])
        return str(output)

if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel

    async def run_test():
        console = Console()
        console.print(Panel.fit("[bold cyan]Email Agent: Multi-Server Logic Test[/bold cyan]"))
        
        agent = EmailAssistantAgent()
        await agent.initialize()

        test_queries = [
            "Check for any unread emails from last Monday."
        ]

        for query in test_queries:
            console.print(f"\n[bold yellow]User:[/bold yellow] {query}")
            response = await agent.answer_query(query)
            console.print(Panel(response, title="[bold green]Final Agent Output[/bold green]", border_style="green"))

    asyncio.run(run_test())