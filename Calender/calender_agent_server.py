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
from calender_agent import SchedulerAgent

class SchedulerAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = None
        self._lock = asyncio.Lock()
        self._active_tasks = {}

    async def _ensure_agent(self):
        async with self._lock:
            if self.agent is None:
                self.agent = await SchedulerAgent().initialize()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        await self._ensure_agent()
        task_id = context.task_id
        
        user_id = context.get_metadata().get("user_id", "default_user")

        async def run_process():
            try:
                user_query = context.get_user_input()
                response = await self.agent.answer_query(user_query, user_id)
                
                if task_id in self._active_tasks:
                    await event_queue.enqueue_event(new_agent_text_message(response))
            except asyncio.CancelledError:
                raise

        task = asyncio.create_task(run_process())
        self._active_tasks[task_id] = task
        try:
            await task
        finally:
            self._active_tasks.pop(task_id, None)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        if task_id in self._active_tasks:
            self._active_tasks[task_id].cancel()

def main():
    load_dotenv()
    host = os.environ.get("AGENT_HOST", "localhost")
    port = int(os.environ.get("SCHEDULER_AGENT_PORT", 9002))
    
    skill = AgentSkill(
        id="scheduler_service",
        name="Calendar Logic",
        description="Autonomous calendar management and scheduling service with multi-user support.",
        tags=["calendar", "mcp", "scheduling"],
        examples=["Am I free today?", "Schedule a meeting for tomorrow at 10am","Cancel my meeting with john next week."]
    )
    
    agent_card = AgentCard(
        name="SchedulerAgent",
        description="A2A Scheduler Agent powered by MCP.",
        url=f"http://{host}:{port}/",
        version="1.5.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill]
    )
    
    handler = DefaultRequestHandler(
        agent_executor=SchedulerAgentExecutor(), 
        task_store=InMemoryTaskStore()
    )
    
    app = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=handler
    )
    
    uvicorn.run(app.build(), host=host, port=port)

if __name__ == "__main__":
    main()