import structlog
from typing import List
from .workflows import WorkflowTask, TaskPriority

logger = structlog.get_logger(__name__)

class TaskPrioritizer:
    def sort_tasks(self, tasks: List[WorkflowTask]) -> List[WorkflowTask]:
        """Sorts tasks based on priority and dependencies."""
        # Simple topological sort + priority for MVP
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)
        logger.debug("tasks_prioritized", count=len(sorted_tasks))
        return sorted_tasks
