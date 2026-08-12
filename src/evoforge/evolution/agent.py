import structlog
from typing import Dict, Any, List
from evoforge.model_router.router import ModelRouter, LLMRequest
from evoforge.model_router.classifier import TaskType, TaskComplexity
from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry

logger = structlog.get_logger(__name__)

class EvolutionAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry):
        super().__init__(
            name="EvolutionAgent",
            role="Analyze system performance, analyze failing workflows, and propose code improvements to the EvoForge system itself.",
            model_router=model_router,
            tools=tools
        )
        
    def analyze_failures(self, failure_logs: str) -> str:
        """Analyzes a batch of failure logs and proposes self-improvement patches."""
        task_prompt = f"Analyze the following failure logs from recent EvoForge workflows and propose patches to our internal logic to prevent them:\n\n{failure_logs}"
            
        return self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.CRITICAL
        )
