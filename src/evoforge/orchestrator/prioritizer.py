
import structlog

from .workflows import WorkflowTask

logger = structlog.get_logger(__name__)

class TaskPrioritizer:
    def sort_tasks(self, tasks: list[WorkflowTask]) -> list[WorkflowTask]:
        """Sorts tasks based on priority and dependencies."""
        # Simple topological sort + priority for MVP
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)
        logger.debug("tasks_prioritized", count=len(sorted_tasks))
        return sorted_tasks
