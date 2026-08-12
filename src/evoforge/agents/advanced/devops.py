from evoforge.agents.base import BaseAgent
from evoforge.model_router.router import ModelRouter
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskType, TaskComplexity

class DevOpsAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="DevOpsAgent",
            role="Manage CI/CD pipelines, Dockerfiles, and deployment scripts.",
            model_router=model_router,
            tools=tools
        )
        
    def setup_pipeline(self, tech_stack: str) -> str:
        return self.think_and_act(
            task_description=f"Create a CI/CD pipeline for a {tech_stack} project.",
            task_type=TaskType.CODE_GENERATION,
            complexity=TaskComplexity.HIGH
        )
