from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter


class QAAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="QAAgent",
            role="Write tests, execute test suites using execute_command, and verify code correctness. Ensure full coverage for new features.",
            model_router=model_router,
            tools=tools
        )
        
    def write_tests(self, target_file: str, test_file: str) -> str:
        """Entry point for writing tests."""
        task_prompt = f"Write unit tests for the code in {target_file}. Save the tests to {test_file} and execute them to verify."
            
        return self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.CODE_GENERATION,
            complexity=TaskComplexity.MEDIUM
        )
