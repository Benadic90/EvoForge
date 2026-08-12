from evoforge.agents.base import BaseAgent
from evoforge.model_router.router import ModelRouter
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.classifier import TaskType, TaskComplexity

class SecurityAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="SecurityAgent",
            role="Audit code for security vulnerabilities, secrets, injection flaws, and unsafe practices.",
            model_router=model_router,
            tools=tools
        )
        
    def audit_code(self, target_file: str) -> str:
        """Entry point for security auditing."""
        task_prompt = f"Perform a security audit on the file {target_file}. Identify vulnerabilities like XSS, SQLi, SSRF, or leaked secrets."
            
        return self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.SECURITY_ANALYSIS,
            complexity=TaskComplexity.CRITICAL
        )
