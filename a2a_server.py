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

from agents import PolicyAgent 

class GenericAgentExecutor(AgentExecutor):
    def __init__(self, agent_instance):
        self.agent = agent_instance
        self.active_tasks = set()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        self.active_tasks.add(task_id)
        try:
            prompt = context.get_user_input()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.agent.answer_query, prompt)
            
            if task_id in self.active_tasks:
                message = new_agent_text_message(response)
                await event_queue.enqueue_event(message)
        finally:
            self.active_tasks.discard(task_id)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        if task_id in self.active_tasks:
            self.active_tasks.discard(task_id)

class AgentServer:
    def __init__(self, agent_instance, name, description, skill_details, port_key):
        load_dotenv()
        self.agent_instance = agent_instance
        self.name = name
        self.description = description
        self.skill_details = skill_details
        self.port = int(os.environ.get(port_key, 9999))
        self.host = os.environ.get("AGENT_HOST", "localhost")

    def _build_card(self):
        skill = AgentSkill(
            id=self.skill_details["id"],
            name=self.skill_details["name"],
            description=self.skill_details["description"],
            tags=self.skill_details.get("tags", []),
            examples=self.skill_details.get("examples", []),
        )
        return AgentCard(
            name=self.name,
            description=self.description,
            url=f"http://{self.host}:{self.port}/",
            version="1.0.0",
            default_input_modes=["text/plain"],
            default_output_modes=["text/plain"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[skill],
        )

    def serve(self):
        card = self._build_card()
        handler = DefaultRequestHandler(
            agent_executor=GenericAgentExecutor(self.agent_instance),
            task_store=InMemoryTaskStore(),
        )
        
        server_app = A2AStarletteApplication(
            agent_card=card,
            http_handler=handler,
        )
        
        uvicorn.run(server_app.build(), host=self.host, port=self.port)

if __name__ == "__main__":
    policy_skill = {
        "id": "insurance_coverage",
        "name": "Insurance coverage",
        "description": "Provides information about insurance coverage options and details.",
        "tags": ["insurance", "coverage"],
        "examples": ["What does my policy cover?", "Are mental health services included?"],
    }

    server = AgentServer(
        agent_instance=PolicyAgent(),
        name="InsurancePolicyCoverageAgent",
        description="Provides information about insurance policy coverage options and details.",
        skill_details=policy_skill,
        port_key="POLICY_AGENT_PORT"
    )
    
    server.serve()