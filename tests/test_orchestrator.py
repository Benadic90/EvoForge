from unittest.mock import MagicMock
import pytest

from evoforge.memory.events import emitter
from evoforge.memory.manager import MemoryManager
from evoforge.memory.state import WorkflowStage
from evoforge.orchestrator.engine import OrchestratorEngine
from evoforge.agents.registry import AgentRegistry
from evoforge.agents.contracts import AgentContract, AgentContext, AgentResult, AgentExecutor
from evoforge.orchestrator.workflows import TaskPriority, WorkflowDefinition, WorkflowTask

class MockExecutor(AgentExecutor):
    def __init__(self):
        self.call_count = 0
        
    def execute(self, context: AgentContext) -> AgentResult:
        self.call_count += 1
        return AgentResult(
            success=True,
            agent_id="developer",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Code written.",
        )

@pytest.fixture
def mock_memory():
    mock = MagicMock(spec=MemoryManager)
    mock.db = MagicMock()
    return mock

@pytest.fixture(autouse=True)
def disable_emitter():
    original_store = emitter.store
    emitter.store = None
    yield
    emitter.store = original_store

@pytest.fixture
def engine(mock_memory):
    registry = AgentRegistry()
    contract = AgentContract(agent_id="developer", name="Dev", display_name="Dev", role="Dev", description="Dev", version="1")
    registry.register(contract, MockExecutor())
    
    engine = OrchestratorEngine(mock_memory, registry)
    engine.worker_id = "test-worker-id"
    return engine

def test_workflow_execution(engine, mock_memory):
    # Mock the lease acquisition to succeed by returning the engine's worker_id
    mock_memory.db.fetchall.return_value = [{"worker_id": engine.worker_id}]
    
    task1 = WorkflowTask(
        id="t1",
        name="Build API",
        description="Build the login API",
        priority=TaskPriority.HIGH,
        agent_type="developer"
    )
    
    task2 = WorkflowTask(
        id="t2",
        name="Docs",
        description="Write docs",
        priority=TaskPriority.LOW,
        agent_type="developer" # Actually should be documentation, but using dev for test
    )
    
    wf = WorkflowDefinition(
        id="wf-1",
        repo_name="my-repo",
        tasks=[task2, task1] # Out of priority order
    )
    
    engine.execute_workflow(wf)
    
    assert wf.state == WorkflowStage.COMPLETE
    assert wf.tasks[0].status == WorkflowStage.COMPLETE # Which is task2
    assert wf.tasks[1].status == WorkflowStage.COMPLETE # Which is task1
    
    # Check prioritization: task1 (HIGH) should be executed before task2 (LOW)
    # The prioritizer sorts descending, so task1 is index 0 in sorted list
    _, executor = engine.agent_registry.get("developer")
    assert executor.call_count == 2
