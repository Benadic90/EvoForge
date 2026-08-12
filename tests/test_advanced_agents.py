import pytest
from unittest.mock import MagicMock
from evoforge.agents.advanced.planner import PlannerAgent
from evoforge.agents.advanced.architect import ArchitectAgent
from evoforge.agents.advanced.devops import DevOpsAgent
from evoforge.agents.advanced.documentation import DocumentationAgent
from evoforge.agents.advanced.research import ResearchAgent
from evoforge.agents.advanced.conflict_resolver import ConflictResolver
from evoforge.model_router.router import ModelRouter, LLMResponse
from evoforge.agents.registry import ToolRegistry

def test_advanced_agents_init():
    router = MagicMock(spec=ModelRouter)
    tools = ToolRegistry()
    
    planner = PlannerAgent(router, tools)
    assert planner.name == "PlannerAgent"
    
    architect = ArchitectAgent(router, tools)
    assert architect.name == "ArchitectAgent"
    
    devops = DevOpsAgent(router, tools)
    assert devops.name == "DevOpsAgent"
    
    docs = DocumentationAgent(router, tools)
    assert docs.name == "DocumentationAgent"
    
    research = ResearchAgent(router, tools)
    assert research.name == "ResearchAgent"
    
def test_conflict_resolver():
    router = MagicMock(spec=ModelRouter)
    mock_response = LLMResponse(
        content="Opinion A is better because...",
        provider="test",
        model="test",
        input_tokens=10,
        output_tokens=10,
        cost_usd=0.0,
        latency_ms=10
    )
    router.complete.return_value = mock_response
    
    resolver = ConflictResolver(router)
    result = resolver.resolve("Use SQL vs NoSQL", "SQL is ACID", "NoSQL is scale")
    
    assert "Opinion A is better" in result
    router.complete.assert_called_once()
