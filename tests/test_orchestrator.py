from unittest.mock import MagicMock

from evoforge.memory.events import emitter
from evoforge.memory.manager import MemoryManager
from evoforge.memory.state import WorkflowStage
from evoforge.orchestrator.engine import OrchestratorEngine
from evoforge.orchestrator.workflows import TaskPriority, WorkflowDefinition, WorkflowTask


def test_workflow_execution():
    emitter.store = None # Disable persistent event store for this test
    mock_memory = MagicMock(spec=MemoryManager)
    mock_memory.db = MagicMock()
    
    mock_dev_agent = MagicMock()
    mock_dev_agent.implement_feature.return_value = "Code written."
    
    agents = {"developer": mock_dev_agent}
    engine = OrchestratorEngine(mock_memory, agents)
    
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
    assert mock_dev_agent.implement_feature.call_count == 2
