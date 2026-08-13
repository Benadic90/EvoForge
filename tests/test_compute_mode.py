import pytest
import json
from evoforge.memory.database import Database
from evoforge.model_router.compute_policy import ComputePolicy
from evoforge.model_router.routing import ExecutorRouter
from evoforge.model_router.executors import ExecutorRegistry, LocalModelExecutor, GeminiExecutor
from evoforge.model_router.requirements import TaskRequirements, TaskClassification
from evoforge.agents.capabilities import AgentCapability

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_compute.db"
    return Database(str(db_path))

@pytest.fixture
def mock_registry():
    registry = ExecutorRegistry()
    registry.register("ollama", LocalModelExecutor(), [AgentCapability.CODING])
    registry.register("gemini", GeminiExecutor(), [AgentCapability.CODING])
    registry.set_health("ollama", True)
    registry.set_health("gemini", True)
    return registry

@pytest.fixture
def test_reqs():
    return TaskRequirements(
        task_id="test_compute",
        task_type=TaskClassification.CODING,
        required_capabilities=[AgentCapability.CODING]
    )

def test_compute_policy_persistence(test_db):
    policy = ComputePolicy(mode="LOCAL", prefer_local=True)
    policy.save_to_db(test_db)
    
    loaded = ComputePolicy.load_from_db(test_db)
    assert loaded.mode == "LOCAL"
    assert loaded.prefer_local is True

def test_local_mode_excludes_cloud(test_db, mock_registry, test_reqs):
    policy = ComputePolicy(mode="LOCAL")
    policy.save_to_db(test_db)
    
    router = ExecutorRouter(mock_registry, memory_manager=test_db)
    _, expl = router.get_candidate_chain(test_reqs)
    
    # gemini should be rejected, ollama selected
    assert expl.selected_executor_id == "ollama"
    assert "gemini" in expl.rejected

def test_cloud_mode_excludes_local(test_db, mock_registry, test_reqs):
    policy = ComputePolicy(mode="CLOUD")
    policy.save_to_db(test_db)
    
    router = ExecutorRouter(mock_registry, memory_manager=test_db)
    _, expl = router.get_candidate_chain(test_reqs)
    
    # ollama should be rejected, gemini selected
    assert expl.selected_executor_id == "gemini"
    assert "ollama" in expl.rejected

def test_hybrid_mode_allows_both(test_db, mock_registry, test_reqs):
    policy = ComputePolicy(mode="HYBRID")
    policy.save_to_db(test_db)
    
    router = ExecutorRouter(mock_registry, memory_manager=test_db)
    _, expl = router.get_candidate_chain(test_reqs)
    
    # Both should be candidates (no systemic compute mode rejections)
    candidate_ids = [c.executor_id for c in expl.candidates]
    assert "ollama" in candidate_ids
    assert "gemini" in candidate_ids

def test_local_disabled_by_policy(test_db, mock_registry, test_reqs):
    policy = ComputePolicy(mode="HYBRID", ollama_enabled=False)
    policy.save_to_db(test_db)
    
    router = ExecutorRouter(mock_registry, memory_manager=test_db)
    chain, expl = router.get_candidate_chain(test_reqs)
    
    assert "ollama" in expl.rejected
    assert expl.rejected["ollama"][0] == "Local executor explicitly disabled by policy."
