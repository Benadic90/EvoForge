from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.cost_tracker import CostTracker
from evoforge.model_router.router import LLMRequest, ModelRouter


def test_model_router_initialization():
    router = ModelRouter()
    assert "gemini" in router.providers
    assert "ollama" in router.providers

def test_cost_tracker():
    tracker = CostTracker(daily_budget_usd=5.00)
    assert tracker.can_afford(1.00) == True
    
    tracker.record_cost(4.50, provider="gemini")
    assert tracker.spent_today_usd == 4.50
    
    assert tracker.can_afford(1.00) == False
    
    tracker.reset_daily()
    assert tracker.spent_today_usd == 0.0
    assert tracker.can_afford(1.00) == True

def test_router_selection_logic():
    router = ModelRouter()
    
    # Test simple task routing (should pick local if available)
    req1 = LLMRequest(
        prompt="Format this json",
        task_type=TaskType.CLASSIFICATION,
        complexity=TaskComplexity.TRIVIAL
    )
    provider, model = router._select_model(req1)
    assert provider == "ollama"
    
    # Test complex task routing (should default to gemini)
    req2 = LLMRequest(
        prompt="Design a distributed database architecture",
        task_type=TaskType.PLANNING,
        complexity=TaskComplexity.HIGH
    )
    provider, model = router._select_model(req2)
    assert provider == "gemini"
