import asyncio
import os
from typing import Any, List, Dict
from dotenv import load_dotenv

from beeai_framework.adapters.a2a.serve.server import A2AServer, A2AServerConfig
from beeai_framework.adapters.a2a.agents import A2AAgent
from beeai_framework.adapters.vertexai import VertexAIChatModel
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.middleware.trajectory import EventMeta, GlobalTrajectoryMiddleware
from beeai_framework.serve.utils import LRUMemoryManager
from beeai_framework.tools import Tool
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.tools.think import ThinkTool

from helpers import authenticate

class ConciseGlobalTrajectoryMiddleware(GlobalTrajectoryMiddleware):
    def _format_prefix(self, meta: EventMeta) -> str:
        prefix = super()._format_prefix(meta)
        return prefix.rstrip(": ")

    def _format_payload(self, value: Any) -> str:
        return ""

class A2AOrchestrator:
    def __init__(self):
        load_dotenv()
        self.credentials, self.project_id = authenticate()
        self.host = os.environ.get("AGENT_HOST", "localhost")
        self.manager_port = int(os.environ.get("HEALTHCARE_AGENT_PORT", 8000))
        self.sub_agent_configs = [
            {"name": "PolicyAgent", "port": os.environ.get("POLICY_AGENT_PORT")},
            {"name": "ResearchAgent", "port": os.environ.get("RESEARCH_AGENT_PORT")},
            {"name": "ProviderAgent", "port": os.environ.get("PROVIDER_AGENT_PORT")},
        ]
        self.sub_agents = []
        self.handoff_tools = []

    async def _setup_sub_agents(self):
        for config in self.sub_agent_configs:
            agent = A2AAgent(
                url=f"http://{self.host}:{config['port']}", 
                memory=UnconstrainedMemory()
            )
            await agent.check_agent_exists()
            self.sub_agents.append(agent)
            
            tool = HandoffTool(
                target=agent,
                name=agent.name,
                description=agent.agent_card.description
            )
            self.handoff_tools.append(tool)
            print(f"Initialized sub-agent: {agent.name}")

    def _create_manager(self):
        think_tool = ThinkTool()
        
        agent = RequirementAgent(
            name="Healthcare Orchestrator",
            description="Manager agent coordinating specialist sub-agents.",
            llm=VertexAIChatModel(
                model_id="gemini-1.5-flash",
                project=self.project_id,
                location="us-central1",
                allow_parallel_tool_calls=True
            ),
            tools=[think_tool] + self.handoff_tools,
            requirements=[
                ConditionalRequirement(think_tool, force_at_step=1, consecutive_allowed=False),
                *[ConditionalRequirement(t, consecutive_allowed=False) for t in self.handoff_tools]
            ],
            role="Orchestrator",
            instructions="Route user queries to the appropriate specialist agent and summarize the results."
        )
        return agent

    async def start(self):
        await self._setup_sub_agents()
        manager = self._create_manager()
        
        server = A2AServer(
            config=A2AServerConfig(port=self.manager_port, protocol="jsonrpc", host=self.host),
            memory_manager=LRUMemoryManager(maxsize=100),
        )
        
        print(f"Server starting on {self.host}:{self.manager_port}")
        server.register(manager, send_trajectory=True).serve()

if __name__ == "__main__":
    orchestrator = A2AOrchestrator()
    asyncio.run(orchestrator.start())