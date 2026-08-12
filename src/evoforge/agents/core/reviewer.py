from evoforge.agents.base import BaseAgent
from evoforge.model_router.router import ModelRouter
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskType, TaskComplexity

class ReviewerAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="ReviewerAgent",
            role="Review code changes for style, architecture, logic errors, and best practices. Provide feedback or fix the issues directly.",
            model_router=model_router,
            tools=tools
        )
        
    def review_changes(self, diff_content: str) -> str:
        """Entry point for code review."""
        task_prompt = f"Review the following code changes. Identify logic errors, architectural flaws, or style violations:\n\n{diff_content}"
            
        return self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.CODE_REVIEW,
            complexity=TaskComplexity.HIGH
        )
