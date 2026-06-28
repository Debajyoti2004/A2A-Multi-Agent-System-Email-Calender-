import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.gemini.backend.chat import GeminiChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool

class VerboseThoughtMiddleware(GlobalTrajectoryMiddleware):
    def _format_prefix(self, meta: EventMeta) -> str:
        agent_name = meta.get("agent_name", "Orchestrator")
        return f"[{agent_name}]"

    def _format_payload(self, value: Any) -> str:
        if not value: return ""
        if isinstance(value, str):
            return f"\n🧠 INTERNAL REASONING:\n{value.strip()}\n"
        if hasattr(value, "tool_name") or (isinstance(value, dict) and "tool_name" in value):
            name = getattr(value, "tool_name", value.get("tool_name"))
            return f"➔ DELEGATING TASK TO: {name}"
        if isinstance(value, dict) and "result" in value:
            return f"📥 SPECIALIST RESPONSE RECEIVED: {str(value['result'])[:500]}..."
        return ""

class EmailAssistantOrchestrator:
    def __init__(self):
        load_dotenv()
        self.host = os.environ.get("AGENT_HOST", "localhost")
        self.orchestrator_port = int(os.environ.get("ORCHESTRATOR_PORT", 8000))
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.agent_configs = [
            {"name": "EmailAgent", "url": f"http://{self.host}:9001"},
            {"name": "SchedulerAgent", "url": f"http://{self.host}:9002"}
        ]
        self.handoff_tools = []

    async def _initialize_specialists(self):
        for config in self.agent_configs:
            proxy = A2AAgent(url=config["url"], memory=UnconstrainedMemory())
            await proxy.check_agent_exists()
            
            tool = HandoffTool(
                target=proxy,
                name=proxy.name,
                description=proxy.agent_card.description
            )
            self.handoff_tools.append(tool)

    def _build_brain(self):
        think_tool = ThinkTool()
        
        llm = GeminiChatModel(
            model_id="gemini-1.5-flash",
            api_key=self.api_key,
            allow_parallel_tool_calls=True
        )
        
        manager = RequirementAgent(
            name="Assistant Orchestrator",
            llm=llm,
            tools=[think_tool] + self.handoff_tools,
            middleware=[VerboseThoughtMiddleware()],
            requirements=[
                ConditionalRequirement(think_tool, force_at_step=1, consecutive_allowed=False),
                *[ConditionalRequirement(t, consecutive_allowed=False) for t in self.handoff_tools]
            ],
            role="AI Chief of Staff",
            instructions=(
                "You are an expert AI Chief of Staff. You manage workspace operations using specialized agents.\n\n"
                "USER IDENTITY MANAGEMENT:\n"
                "1. Access the 'user_id' from the current session metadata.\n"
                "2. When delegating tasks to SchedulerAgent, you MUST explicitly include the 'user_id' in your prompt to ensure the specialist retrieves the correct user data.\n"
                "3. Treat all scheduling requests as identity-specific.\n\n"
                "WORKFLOW:\n"
                "1. Use ThinkTool to plan the orchestration sequence.\n"
                "2. Call EmailAgent for mail threads, triage, and smart searches.\n"
                "3. Call SchedulerAgent for availability and calendar events.\n"
                "4. Execute parallel tool calls when a query involves both agents.\n"
                "5. Provide a consolidated final response stating which agent performed which action."
            )
        )
        return manager

    async def run(self):
        await self._initialize_specialists()
        brain = self._build_brain()
        
        server = A2AServer(
            config=A2AServerConfig(port=self.orchestrator_port, protocol="jsonrpc", host=self.host),
            memory_manager=LRUMemoryManager(maxsize=100),
        )
        
        server.register(brain, send_trajectory=True).serve()

if __name__ == "__main__":
    orchestrator = EmailAssistantOrchestrator()
    asyncio.run(orchestrator.run())