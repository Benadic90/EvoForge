import structlog
import time
from typing import Dict, Any, List

from .workflows import WorkflowDefinition, WorkflowState, WorkflowTask
from .prioritizer import TaskPrioritizer
from evoforge.memory.manager import MemoryManager

logger = structlog.get_logger(__name__)

class OrchestratorEngine:
    def __init__(self, memory_manager: MemoryManager, agent_roster: Dict[str, Any], learning_system: Any = None):
        self.memory = memory_manager
        self.agents = agent_roster
        self.prioritizer = TaskPrioritizer()
        self.learning = learning_system

    def execute_workflow(self, workflow: WorkflowDefinition):
        """Executes a workflow by delegating to specific agents."""
        logger.info("workflow_started", workflow_id=workflow.id, repo=workflow.repo_name)
        workflow.state = WorkflowState.RUNNING
        self.memory.record_workflow_checkpoint(workflow.id, workflow.state.value, {})
        
        try:
            sorted_tasks = self.prioritizer.sort_tasks(workflow.tasks)
            
            for task in sorted_tasks:
                if task.status == WorkflowState.COMPLETED:
                    continue
                    
                self._execute_task(task, workflow)
                
            workflow.state = WorkflowState.COMPLETED
            logger.info("workflow_completed", workflow_id=workflow.id)
            
        except Exception as e:
            workflow.state = WorkflowState.CRASHED
            logger.error("workflow_crashed", workflow_id=workflow.id, error=str(e))
        finally:
            self.memory.record_workflow_checkpoint(workflow.id, workflow.state.value, {"last_task_count": len(workflow.tasks)})

    def _execute_task(self, task: WorkflowTask, workflow: WorkflowDefinition):
        task.status = WorkflowState.RUNNING
        agent = self.agents.get(task.agent_type)
        
        if not agent:
            task.status = WorkflowState.FAILED
            logger.error("agent_not_found", agent_type=task.agent_type, task_id=task.id)
            return

        logger.info("task_started", task_id=task.id, agent=task.agent_type)
        
        try:
            # MVP: Map standard task types to agent methods statically
            # In a real system, the task would specify the action dynamically
            if task.agent_type == "developer":
                result = agent.implement_feature(task.description, context_files=[])
            elif task.agent_type == "qa":
                result = agent.write_tests(task.description, "test_output.py")
            elif task.agent_type == "reviewer":
                result = agent.review_changes(task.description)
            elif task.agent_type == "security":
                result = agent.audit_code(task.description)
            else:
                result = agent.think_and_act(task.description, task_type=None, complexity=None) # Fallback for advanced agents
                
            task.context["result"] = result
            task.status = WorkflowState.COMPLETED
            logger.info("task_completed", task_id=task.id)
            
            # Record outcome for learning system
            if self.learning:
                details = {"description": task.description, "context": task.context}
                self.learning.record_outcome(task.agent_type, task.id, True, details)
            
        except Exception as e:
            task.status = WorkflowState.FAILED
            task.context["error"] = str(e)
            logger.error("task_failed", task_id=task.id, error=str(e))
            
            # Record outcome for learning system
            if self.learning:
                details = {"description": task.description, "error_message": str(e), "attempted_solution": task.context.get("result", "")}
                self.learning.record_outcome(task.agent_type, task.id, False, details)
                
            raise

    def recover_crashed_workflows(self):
        """Scans database for crashed/running workflows on startup and recovers them."""
        # MVP placeholder. Real impl would query SQLite for state IN (RUNNING, CRASHED)
        logger.info("crash_recovery_scan_completed")

    def run_daily_loop(self, workflows: List[WorkflowDefinition]):
        """The main autonomous loop triggered daily."""
        logger.info("daily_loop_started")
        self.recover_crashed_workflows()
        
        for wf in workflows:
            self.execute_workflow(wf)
            
        # Log daily summary to Obsidian
        summary = f"# Daily Loop Results\nProcessed {len(workflows)} workflows."
        self.memory.log_daily_summary(summary)
        
        # Run scheduled research after main work
        if self.learning and hasattr(self.learning, 'run_scheduled_research'):
            self.learning.run_scheduled_research()
            
        if self.learning and hasattr(self.learning, 'check_stale_skills'):
            self.learning.check_stale_skills()
        
        logger.info("daily_loop_finished")
