from unittest.mock import MagicMock

from evoforge.agents.core.developer import DeveloperAgent
from evoforge.agents.core.qa import QAAgent
from evoforge.agents.core.reviewer import ReviewerAgent
from evoforge.agents.core.security import SecurityAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.model_router.router import LLMResponse, ModelRouter


def test_core_agents_init():
    router = MagicMock(spec=ModelRouter)
    tools = ToolRegistry()
    
    dev = DeveloperAgent(router, tools)
    assert dev.name == "DeveloperAgent"
    
    qa = QAAgent(router, tools)
    assert qa.name == "QAAgent"
    
    reviewer = ReviewerAgent(router, tools)
    assert reviewer.name == "ReviewerAgent"
    
    security = SecurityAgent(router, tools)
    assert security.name == "SecurityAgent"

def test_developer_agent_flow():
    # Setup mocks
    router = MagicMock(spec=ModelRouter)
    
    # Mock fallback manager instead of router directly since BaseAgent uses fallback manager
    # We will mock the complete_with_fallback method
    
    tools = ToolRegistry()
    dev = DeveloperAgent(router, tools)
    
    mock_response = LLMResponse(
        content="I have implemented the feature. No tools needed.",
        provider="test",
        model="test",
        input_tokens=10,
        output_tokens=10,
        cost_usd=0.0,
        latency_ms=10
    )
    
    # Mock the fallback manager's method
    dev.fallback_manager.complete_with_fallback = MagicMock(return_value=mock_response)
    
    result = dev.implement_feature("Add a login button", ["src/ui.py"])
    
    assert "I have implemented the feature" in result
    dev.fallback_manager.complete_with_fallback.assert_called_once()
