from evoforge.agents.base import BaseAgent
from evoforge.model_router.router import ModelRouter
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskType, TaskComplexity

class PlannerAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="PlannerAgent",
            role="Break down complex user requests into smaller actionable tasks for other agents to execute.",
            model_router=model_router,
            tools=tools
        )
        
    def generate_plan(self, goal: str) -> str:
        """Entry point for generating a project plan."""
        return self.think_and_act(
            task_description=f"Create a step-by-step implementation plan for: {goal}",
            task_type=TaskType.PLANNING,
            complexity=TaskComplexity.HIGH
        )
