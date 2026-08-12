
import structlog

from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import LLMRequest, ModelRouter

logger = structlog.get_logger(__name__)

class ConflictResolver:
    def __init__(self, model_router: ModelRouter):
        self.router = model_router
        
    def resolve(self, issue_description: str, agent_a_opinion: str, agent_b_opinion: str) -> str:
        """Resolves a conflict between two agents using an LLM as a mediator."""
        prompt = (
            f"There is a conflict regarding: {issue_description}\n\n"
            f"Opinion A:\n{agent_a_opinion}\n\n"
            f"Opinion B:\n{agent_b_opinion}\n\n"
            "Analyze both opinions and provide a final, objective resolution."
        )
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are a senior principal engineer resolving technical disputes.",
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.HIGH
        )
        
        try:
            response = self.router.complete(request)
            logger.info("conflict_resolved")
            return response.content
        except Exception as e:
            logger.error("conflict_resolution_failed", error=str(e))
            return "Fallback resolution: Defer to human review."


ConflictResolverAgent = ConflictResolver

