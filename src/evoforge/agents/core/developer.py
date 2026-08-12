from evoforge.agents.base import BaseAgent
from evoforge.model_router.router import ModelRouter
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskType, TaskComplexity

class DeveloperAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="DeveloperAgent",
            role="Write, edit, and refactor code to implement features and fix bugs. You use the read_file and write_file tools to modify the codebase.",
            model_router=model_router,
            tools=tools
        )
        
    def implement_feature(self, description: str, context_files: list[str]) -> str:
        """Entry point for feature implementation."""
        task_prompt = f"Implement the following feature: {description}\n\nRelevant files:\n"
        for f in context_files:
            task_prompt += f"- {f}\n"
            
        return self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.CODE_GENERATION,
            complexity=TaskComplexity.HIGH
        )
