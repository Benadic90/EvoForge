from datetime import UTC, datetime, timedelta

import structlog

from evoforge.memory.database import Database
from evoforge.memory.idempotency import IdempotencyManager
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager
from evoforge.memory.state import WorkflowStage, WorkflowState
from evoforge.orchestrator.engine import OrchestratorEngine
from evoforge.orchestrator.workflows import WorkflowDefinition, WorkflowTask
from evoforge.agents.registry import AgentRegistry
from evoforge.agents.contracts import AgentContract, AgentContext, AgentResult, AgentExecutor

logger = structlog.get_logger(__name__)

class MockExecutor(AgentExecutor):
    def __init__(self, id_val: str = "developer", fail_first: bool = False):
        self.id_val = id_val
        self.fail_first = fail_first
        self.calls = 0
        
    def execute(self, context: AgentContext) -> AgentResult:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise ValueError("Transient error")
        return AgentResult(
            success=True,
            agent_id=self.id_val,
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary=f"executed by {self.id_val}"
        )

def setup_env(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    obs = ObsidianManager(str(tmp_path / "obsidian"))
    manager = MemoryManager(db, obs)
    manager.init_memory_systems()
    return db, manager

def test_workflow_crash_recovery_resumes_execution(tmp_path):
    db, manager = setup_env(tmp_path)
    
    registry = AgentRegistry()
    executor = MockExecutor()
    contract = AgentContract(agent_id="developer", name="Dev", display_name="Dev", role="Dev", description="Dev", version="1")
    registry.register(contract, executor)
    
    engine = OrchestratorEngine(manager, registry)
    
    # 1. Define workflow and inject a partially completed state
    task1 = WorkflowTask(id="task_1", name="Task 1", description="Implement a feature", priority=1, agent_type="developer")
    workflow_def = WorkflowDefinition(id="wf_123", repo_name="test/repo", tasks=[task1])
    
    db.execute("INSERT INTO workflows (id, project, workflow_type) VALUES (?, ?, ?)", ("wf_123", "test/repo", "test"))
    
    db.execute("INSERT INTO tasks (id, project, task_type, title, description, priority, assigned_workflow) VALUES (?, ?, ?, ?, ?, ?, ?)",
               ("task_1", "test/repo", "developer", "Task 1", "Implement a feature", 1.0, "wf_123"))
    
    state = engine._sync_workflow_definition_to_state(workflow_def, "run_1")
    state.advance_to(WorkflowStage.IMPLEMENT) # We crash AT implement, before tasks run
    
    # Expire the lease to simulate a dead worker
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    db.execute("UPDATE workflows SET lease_expires_at = ? WHERE id = ?", (past, "wf_123"))
    manager.record_workflow_checkpoint(state)
    
    assert executor.calls == 0
    
    # 2. Recover
    engine.recover_crashed_workflows()
    
    # 3. Verify it resumed and executed the task
    assert executor.calls == 1
    rows = db.fetchall("SELECT status FROM workflows WHERE id = ?", ("wf_123",))
    assert rows[0]["status"] == WorkflowStage.COMPLETE.value

def test_workflow_concurrent_locks(tmp_path):
    db, manager = setup_env(tmp_path)
    
    reg_a = AgentRegistry()
    reg_a.register(AgentContract(agent_id="developer", name="DevA", display_name="DevA", role="DevA", description="DevA", version="1"), MockExecutor("devA"))
    engine_A = OrchestratorEngine(manager, reg_a)
    
    reg_b = AgentRegistry()
    reg_b.register(AgentContract(agent_id="developer", name="DevB", display_name="DevB", role="DevB", description="DevB", version="1"), MockExecutor("devB"))
    engine_B = OrchestratorEngine(manager, reg_b)
    
    db.execute("INSERT INTO workflows (id, project, workflow_type) VALUES (?, ?, ?)", ("wf_lock", "test/repo", "test"))
    
    # Engine A acquires lease manually
    got_lease_A = engine_A._acquire_lease("wf_lock")
    assert got_lease_A is True
    
    # Engine B tries to acquire lease
    got_lease_B = engine_B._acquire_lease("wf_lock")
    assert got_lease_B is False # Should fail

def test_idempotency_manager(tmp_path):
    db, manager = setup_env(tmp_path)
    idemp = IdempotencyManager(db)
    
    # First execution
    res1 = idemp.check_operation("wf_1", "CREATE_BRANCH", "task_1")
    assert res1 is None
    
    idemp.record_operation("wf_1", "CREATE_BRANCH", "task_1", "branch_created")
    
    # Second execution
    res2 = idemp.check_operation("wf_1", "CREATE_BRANCH", "task_1")
    assert res2 == "branch_created"

def test_workflow_retry_budget(tmp_path):
    db, manager = setup_env(tmp_path)
    # Agent fails first time, succeeds second
    registry = AgentRegistry()
    executor = MockExecutor("dev1", fail_first=True)
    contract = AgentContract(agent_id="developer", name="Dev", display_name="Dev", role="Dev", description="Dev", version="1")
    registry.register(contract, executor)
    engine = OrchestratorEngine(manager, registry)
    
    task1 = WorkflowTask(id="task_retry", name="Task Retry", description="Retry me", priority=1, agent_type="developer")
    workflow_def = WorkflowDefinition(id="wf_retry", repo_name="test/repo", tasks=[task1])
    db.execute("INSERT INTO workflows (id, project, workflow_type) VALUES (?, ?, ?)", ("wf_retry", "test/repo", "test"))
    
    engine.execute_workflow(workflow_def)
    
    # Assert it was completed eventually because the engine catches the exception and retries
    # Actually wait: The orchestrator's state loop doesn't restart the task if it failed, it just marks the workflow as failed if it exceeds attempts.
    # Ah, the orchestrator handles stage retries! Since IMPLEMENT failed, `execute_stage_logic` raises, it records attempt, loops again.
    
    assert executor.calls == 2
    rows = db.fetchall("SELECT status FROM workflows WHERE id = ?", ("wf_retry",))
    assert rows[0]["status"] == WorkflowStage.COMPLETE.value
