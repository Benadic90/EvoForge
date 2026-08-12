from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter


class DocumentationAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="DocumentationAgent",
            role="Write READMEs, API documentation, and inline code comments.",
            model_router=model_router,
            tools=tools
        )
        
    def write_docs(self, target_file: str) -> str:
        return self.think_and_act(
            task_description=f"Generate documentation for the code in {target_file}.",
            task_type=TaskType.DOCUMENTATION,
            complexity=TaskComplexity.LOW
        )
