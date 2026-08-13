from evoforge.agents.capabilities import AgentCapability
from evoforge.model_router.executors import ExecutorRegistry, GeminiExecutor, LocalModelExecutor
from evoforge.model_router.requirements import TaskRequirements
from evoforge.model_router.routing import ExecutorRouter
from evoforge.runtime.worker import WorkerProfile, WorkerType


class MockMemoryManager:
    pass

class MockWorkerRegistry:
    def __init__(self, laptop_online: bool):
        self.laptop_online = laptop_online
        
    def list_active(self):
        if self.laptop_online:
            return [WorkerProfile(worker_id="laptop-1", worker_type=WorkerType.LAPTOP)]
        return []

def test_laptop_offline_rejects_local():
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor("local_model"), [AgentCapability.CODING])
    registry.register("gemini-flash", GeminiExecutor("gemini-1.5-flash"), [AgentCapability.CODING])
    
    # Mock health checks so they don't fail in tests
    registry.is_healthy = lambda exc_id: True
    
    # Laptop is OFFLINE
    worker_reg = MockWorkerRegistry(laptop_online=False)
    router = ExecutorRouter(registry, memory_manager=None, worker_registry=worker_reg)
    
    req = TaskRequirements(task_id="t1", required_capabilities=["coding"])
    chain, decision = router.get_candidate_chain(req)
    
    # "local" should be rejected
    candidate_ids = [c[0] for c in chain]
    assert "gemini-flash" in candidate_ids
    assert "local" not in candidate_ids
    assert "Laptop worker is offline" in decision.rejected.get("local", [""])[0]

def test_laptop_online_allows_local():
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor("local_model"), [AgentCapability.CODING])
    registry.register("gemini-flash", GeminiExecutor("gemini-1.5-flash"), [AgentCapability.CODING])
    
    registry.is_healthy = lambda exc_id: True
    
    # Laptop is ONLINE
    worker_reg = MockWorkerRegistry(laptop_online=True)
    router = ExecutorRouter(registry, memory_manager=None, worker_registry=worker_reg)
    
    req = TaskRequirements(task_id="t1", required_capabilities=["coding"])
    chain, decision = router.get_candidate_chain(req)
    
    # "local" should be a candidate
    candidate_ids = [c[0] for c in chain]
    assert "local" in candidate_ids
