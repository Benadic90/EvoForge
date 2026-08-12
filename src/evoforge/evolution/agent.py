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

    def propose_skill_update(self, agent_name: str, skill_name: str, failure_logs: str) -> Dict[str, Any]:
        """Proposes changes to an agent's skill based on failures."""
        task_prompt = f"Agent '{agent_name}' has failed repeatedly while using skill '{skill_name}'.\nFailure logs:\n{failure_logs}\n\nBased on these failures, propose specific additions to their techniques, patterns, or anti-patterns to prevent this."
        
        # In a real setup, we would parse JSON output.
        # Stubbing the output parsing for MVP.
        result = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.HIGH
        )
        
        return {
            "proposed_changes": {"patterns": [f"Learn from: {result[:50]}..."]},
            "evidence": f"Analyzed {len(failure_logs.splitlines())} lines of failure logs.",
            "expected_improvement": "Objective improvement in handling edge cases."
        }

    def review_proposal(self, agent_name: str, skill_name: str, proposal_details: str) -> bool:
        """Reviews an innovation proposal to ensure it's objectively sound."""
        task_prompt = f"Review the following skill update proposal for {agent_name} ({skill_name}):\n\n{proposal_details}\n\nIs this a safe and objectively measurable improvement? Reply only YES or NO."
        
        result = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.MEDIUM
        )
        return "YES" in result.upper()
