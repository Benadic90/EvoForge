import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from evoforge.memory.events import emitter
from evoforge.memory.manager import MemoryManager
from evoforge.memory.state import WorkflowStage, WorkflowState
from evoforge.agents.registry import AgentRegistry
from evoforge.agents.contracts import AgentContext
from evoforge.model_router.routing import ExecutorRouter
from evoforge.model_router.requirements import TaskRequirements

from .prioritizer import TaskPrioritizer
from .workflows import WorkflowDefinition, WorkflowTask

logger = structlog.get_logger(__name__)

class OrchestratorEngine:
    def __init__(self, memory_manager: MemoryManager, agent_registry: AgentRegistry, executor_router: ExecutorRouter = None, learning_system: Any = None):
        self.memory = memory_manager
        self.agent_registry = agent_registry
        self.executor_router = executor_router
        self.prioritizer = TaskPrioritizer()
        self.learning = learning_system
        self.worker_id = str(uuid.uuid4())

    def _sync_workflow_definition_to_state(self, workflow_def: WorkflowDefinition, run_id: str) -> WorkflowState:
        return WorkflowState(
            workflow_id=workflow_def.id,
            run_id=run_id,
            repository_id=workflow_def.repo_name,
            current_stage=WorkflowStage.INITIALIZE,
            dry_run=workflow_def.dry_run,
            deadline_at=datetime.now(UTC) + timedelta(hours=2) # 2 hour budget by default
        )

    def _acquire_lease(self, workflow_id: str, duration_minutes: int = 15) -> bool:
        """Atomic lease acquisition using conditional UPDATE."""
        now = datetime.now(UTC).isoformat()
        expires_at = (datetime.now(UTC) + timedelta(minutes=duration_minutes)).isoformat()
        
        query = """
            UPDATE workflows
            SET worker_id = ?, lease_expires_at = ?
            WHERE id = ? AND (lease_expires_at IS NULL OR lease_expires_at < ?)
        """
        self.memory.db.execute(query, (self.worker_id, expires_at, workflow_id, now))
        
        # Check if we successfully got the lease
        rows = self.memory.db.fetchall("SELECT worker_id FROM workflows WHERE id = ?", (workflow_id,))
        if rows and rows[0]["worker_id"] == self.worker_id:
            return True
        return False
        
    def _renew_lease(self, workflow_id: str, duration_minutes: int = 15):
        """Heartbeat to extend the lease."""
        expires_at = (datetime.now(UTC) + timedelta(minutes=duration_minutes)).isoformat()
        query = "UPDATE workflows SET lease_expires_at = ? WHERE id = ? AND worker_id = ?"
        self.memory.db.execute(query, (expires_at, workflow_id, self.worker_id))

    def _execute_stage_logic(self, state: WorkflowState, workflow_def: WorkflowDefinition):
        """Executes logic for a specific stage."""
        if state.current_stage == WorkflowStage.INITIALIZE:
            logger.info("workflow_initialized", workflow=workflow_def.id)
            
        elif state.current_stage == WorkflowStage.PLAN:
            logger.info("workflow_planning", workflow=workflow_def.id)
            
        elif state.current_stage == WorkflowStage.IMPLEMENT:
            sorted_tasks = self.prioritizer.sort_tasks(workflow_def.tasks)
            for task in sorted_tasks:
                if task.status == WorkflowStage.COMPLETE:
                    continue
                self._execute_task(task, state)

    def execute_workflow(self, workflow_def: WorkflowDefinition, state: WorkflowState = None):
        """State-driven execution loop for a workflow."""
        run_id = f"run_{int(time.time())}"
        
        if not state:
            state = self._sync_workflow_definition_to_state(workflow_def, run_id)
            emitter.emit("workflow.started", workflow_id=state.workflow_id, run_id=run_id, repository_id=state.repository_id)
            self.memory.record_workflow_checkpoint(state)
            
        if not self._acquire_lease(state.workflow_id):
            logger.info("workflow_locked_by_other_worker", workflow_id=state.workflow_id)
            return

        try:
            while state.current_stage not in (WorkflowStage.COMPLETE, WorkflowStage.FAILED, WorkflowStage.PAUSED):
                self._renew_lease(state.workflow_id)
                
                # Check budgets
                if state.has_exceeded_deadline():
                    state.mark_failed("Workflow exceeded deadline budget.")
                    break
                if state.has_exceeded_attempts():
                    state.mark_failed("Workflow exceeded max attempts budget.")
                    break
                    
                # Execute current stage
                try:
                    self._execute_stage_logic(state, workflow_def)
                    
                    # Determine next stage
                    next_stage = state.get_next_stage()
                    if next_stage:
                        state.advance_to(next_stage)
                    else:
                        state.mark_completed()
                        
                except Exception as e:
                    state.record_attempt()
                    logger.warning("workflow_stage_failed", stage=state.current_stage.value, error=str(e), attempts=state.attempt_count)
                    if state.has_exceeded_attempts():
                        state.mark_failed(f"Failed stage {state.current_stage.value}: {e!s}")
                        
                self.memory.record_workflow_checkpoint(state)
                
            workflow_def.state = state.current_stage
            
            if state.current_stage == WorkflowStage.COMPLETE:
                emitter.emit("workflow.completed", workflow_id=state.workflow_id, run_id=state.run_id)
            elif state.current_stage == WorkflowStage.FAILED:
                emitter.emit("workflow.failed", workflow_id=state.workflow_id, run_id=state.run_id, error=state.error)

        finally:
            # Release lease
            self.memory.db.execute("UPDATE workflows SET lease_expires_at = NULL WHERE id = ? AND worker_id = ?", (state.workflow_id, self.worker_id))

    def _execute_task(self, task: WorkflowTask, state: WorkflowState):
        if not self.agent_registry.has(task.agent_type):
            logger.error("agent_not_found", agent_type=task.agent_type, task_id=task.id)
            task.status = WorkflowStage.FAILED
            task.context["error"] = f"Agent '{task.agent_type}' not found in registry."
            return
            
        contract, _ = self.agent_registry.get(task.agent_type)
        
        # Build task requirements based on contract
        requirements = TaskRequirements(
            task_id=task.id,
            required_capabilities=contract.capabilities
        )
        
        # Fetch the best executor from the router
        if self.executor_router:
            emitter.emit("router.requested", task_id=task.id, workflow_id=state.workflow_id)
            executor, explanation = self.executor_router.select_executor(requirements)
            emitter.emit("router.executor.selected", 
                         task_id=task.id, 
                         workflow_id=state.workflow_id, 
                         executor_id=explanation.selected_executor_id,
                         score=explanation.score)
        else:
            # Fallback to direct registry executor if no router is provided (for tests)
            _, executor = self.agent_registry.get(task.agent_type)
        
        emitter.emit("task.started", task_id=task.id, workflow_id=state.workflow_id, agent_id=task.agent_type)
        
        try:
            # Construct standard context
            context = AgentContext(
                run_id=state.run_id,
                workflow_id=state.workflow_id,
                task_id=task.id,
                task_description=task.description,
                project_id=state.project_id,
                repository_id=state.repository_id,
                current_stage=state.current_stage,
                dry_run=state.dry_run,
                permissions=[],
                available_tools=[],
                required_capabilities=[],
                memory_context={}
            )
            
            # Execute standard interface
            result = executor.execute(context)
            
            task.status = WorkflowStage.COMPLETE
            task.context["result"] = result.summary
            
            emitter.emit("task.completed", task_id=task.id, workflow_id=state.workflow_id, agent_id=task.agent_type)
            
            if self.learning:
                details = {"complexity": "unknown", "result_summary": result.summary[:100]}
                self.learning.record_outcome(task.agent_type, task.id, result.success, details)
            
        except Exception as e:
            task.status = WorkflowStage.FAILED
            task.context["error"] = str(e)
            emitter.emit("task.failed", task_id=task.id, workflow_id=state.workflow_id, agent_id=task.agent_type, error=str(e))
            
            if self.learning:
                details = {"description": task.description, "error_message": str(e), "attempted_solution": task.context.get("result", "")}
                self.learning.record_outcome(task.agent_type, task.id, False, details)
                
            raise

    def recover_crashed_workflows(self):
        """Scans database for crashed workflows, acquires leases, and resumes them."""
        logger.info("crash_recovery_scan_started")
        now = datetime.now(UTC).isoformat()
        
        # Find workflows that are not terminal, and whose lease is expired or null
        query = """
            SELECT id, state_snapshot FROM workflows 
            WHERE status NOT IN ('COMPLETE', 'FAILED', 'PAUSED')
            AND (lease_expires_at IS NULL OR lease_expires_at < ?)
        """
        rows = self.memory.db.fetchall(query, (now,))
        
        recovered_count = 0
        for row in rows:
            workflow_id = row["id"]
            state_json = row["state_snapshot"]
            
            if state_json:
                try:
                    state = WorkflowState.model_validate_json(state_json)
                    logger.info("workflow_recovered", workflow_id=workflow_id, stage=state.current_stage.value)
                    emitter.emit("workflow.recovered", workflow_id=workflow_id, run_id=state.run_id)
                    
                    # Fetch tasks for this workflow
                    task_rows = self.memory.db.fetchall("SELECT id, title, description, priority, task_type, status FROM tasks WHERE assigned_workflow = ?", (workflow_id,))
                    tasks = []
                    for t in task_rows:
                        tasks.append(WorkflowTask(
                            id=t["id"],
                            name=t["title"],
                            description=t["description"] or "",
                            priority=t["priority"],
                            agent_type=t["task_type"] or "developer",
                        ))
                    
                    # Reconstruct a basic definition to pass to the engine loop
                    workflow_def = WorkflowDefinition(
                        id=workflow_id,
                        repo_name=state.repository_id,
                        tasks=tasks,
                        dry_run=state.dry_run
                    )
                    
                    # Enqueue for execution (resuming state loop)
                    self.execute_workflow(workflow_def, state=state)
                    
                    recovered_count += 1
                except Exception as e:
                    logger.error("workflow_recovery_failed", workflow_id=workflow_id, error=str(e))
            
        logger.info("crash_recovery_scan_completed", recovered_count=recovered_count)

    def run_daily_loop(self, workflows: list[WorkflowDefinition]):
        """The main autonomous loop triggered daily."""
        logger.info("daily_loop_started")
        
        # 1. Recover any crashed workflows
        self.recover_crashed_workflows()
        
        # 2. Execute new workflows
        for wf in workflows:
            self.execute_workflow(wf)
            
        summary = f"# Daily Loop Results\nProcessed {len(workflows)} workflows."
        self.memory.log_daily_summary(summary)
        
        if self.learning and hasattr(self.learning, 'run_scheduled_research'):
            self.learning.run_scheduled_research()
            
        if self.learning and hasattr(self.learning, 'check_stale_skills'):
            self.learning.check_stale_skills()
        
        logger.info("daily_loop_finished")
