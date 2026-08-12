from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter


class ArchitectAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="ArchitectAgent",
            role="Design system architecture, data models, and API contracts.",
            model_router=model_router,
            tools=tools
        )
        
    def design_architecture(self, requirements: str) -> str:
        return self.think_and_act(
            task_description=f"Design the architecture for: {requirements}",
            task_type=TaskType.PLANNING,
            complexity=TaskComplexity.CRITICAL
        )
