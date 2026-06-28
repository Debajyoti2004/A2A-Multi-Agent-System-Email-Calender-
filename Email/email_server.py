import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from email_agent import EmailAssistantAgent
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

class EmailAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = None
        self._lock = asyncio.Lock()
        self._active_tasks = set()

    async def _init_agent(self) -> None:
        async with self._lock:
            if self.agent is None:
                self.agent = await EmailAssistantAgent().initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._init_agent()
        task_id = context.task_id
        self._active_tasks.add(task_id)
        
        try:
            response = await self.agent.answer_query(context.get_user_input())
            if task_id in self._active_tasks:
                await event_queue.enqueue_event(new_agent_text_message(response))
        finally:
            self._active_tasks.discard(task_id)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        if task_id in self._active_tasks:
            self._active_tasks.discard(task_id)

def main():
    load_dotenv()
    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("EMAIL_AGENT_PORT", 9001))
    
    skill = AgentSkill(
        id="email_chief_of_staff",
        name="Email Chief of Staff",
        description="Handles professional email triage, smart search, and SMTP dispatch with relative date reasoning.",
        tags=["gmail", "mcp", "automation", "executive-assistant"],
        examples=[
            "Find all unread emails from last Monday.",
            "Search for emails about 'Invoice' and draft a reply.",
            "Send a professional follow-up to john@example.com."
        ]
    )
    
    card = AgentCard(
        name="EmailChiefOfStaff",
        description="High-performance A2A Agent powered by MCP for total email orchestration.",
        url=f"http://{host}:{port}/",
        version="2.1.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
        defaultInputModes=["text"],  
        defaultOutputModes=["text"]   
    )
    
    handler = DefaultRequestHandler(
        agent_executor=EmailAgentExecutor(), 
        task_store=InMemoryTaskStore()
    )
    
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)
    
    print(f"A2A Server listening on {host}:{port}")
    uvicorn.run(app.build(), host=host, port=port)

if __name__ == "__main__":
    main()