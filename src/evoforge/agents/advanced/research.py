from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter


class ResearchAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="ResearchAgent",
            role="Search the web and read documentation to find solutions to complex problems.",
            model_router=model_router,
            tools=tools
        )
        
    def research_topic(self, topic: str) -> str:
        return self.think_and_act(
            task_description=f"Research the following topic and provide a summary of best practices: {topic}",
            task_type=TaskType.RESEARCH,
            complexity=TaskComplexity.MEDIUM
        )
