import os
import tempfile
from unittest.mock import MagicMock

from evoforge.agents.registry import ToolRegistry
from evoforge.agents.tools import build_tool_registry
from evoforge.model_router.cost_tracker import CostTracker
from evoforge.policy_engine.permissions import PermissionLevel, RepositoryPolicy
from evoforge.policy_engine.validator import ActionValidator


def test_tool_registry():
    registry = ToolRegistry()
    
    def add(a: int, b: int) -> int:
        return a + b
        
    registry.register("add", "Adds two numbers", add)
    
    tool = registry.get_tool("add")
    assert tool.name == "add"
    assert tool.execute(a=2, b=3) == 5
    
def test_built_in_tools_policy_enforcement():
    with tempfile.TemporaryDirectory() as temp_dir:
        policy = RepositoryPolicy(
            repo_name="test",
            level=PermissionLevel.READ_ONLY, # READ ONLY
            forbidden_files=[".env"]
        )
        cost_tracker = CostTracker()
        validator = ActionValidator(policy, cost_tracker)
        mock_repo = MagicMock()
        
        registry = build_tool_registry(temp_dir, validator, mock_repo)
        write_tool = registry.get_tool("write_file")
        exec_tool = registry.get_tool("execute_command")
        
        # Test write (Should fail because READ_ONLY)
        result = write_tool.execute(file_path="test.py", content="print('hello')")
        assert "denied" in result.lower()
        
        # Test execute (Should fail because READ_ONLY)
        result = exec_tool.execute(command="ls")
        assert "denied" in result.lower()
        
        # Upgrade policy
        validator.policy.level = PermissionLevel.READ_WRITE_SANDBOX
        
        # Test write secrets (Should fail because of secrets)
        result = write_tool.execute(file_path="test.py", content="AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
        assert "secrets detected" in result.lower()
        
        # Test write safe (Should pass)
        result = write_tool.execute(file_path="test.py", content="print('hello')")
        assert "successfully" in result.lower()
        assert os.path.exists(os.path.join(temp_dir, "test.py"))
