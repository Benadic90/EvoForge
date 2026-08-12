import os
import subprocess
import structlog
from typing import Dict, Any
from pathlib import Path

from evoforge.policy_engine.validator import ActionValidator
from evoforge.github_integration.repository import LocalRepository
from .registry import ToolRegistry

logger = structlog.get_logger(__name__)

def build_tool_registry(workspace: str, validator: ActionValidator, repo: LocalRepository) -> ToolRegistry:
    registry = ToolRegistry()
    workspace_path = Path(workspace)

    def read_file(file_path: str) -> str:
        """Reads a file from the repository."""
        full_path = workspace_path / file_path
        if not validator.can_read_file(str(full_path)):
            return "Error: Read access denied by policy."
            
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(file_path: str, content: str) -> str:
        """Writes content to a file in the repository."""
        full_path = workspace_path / file_path
        if not validator.can_write_file(str(full_path), content):
            return "Error: Write access denied by policy or secrets detected."
            
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return "File successfully written."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def execute_command(command: str) -> str:
        """Executes a shell command within the repository context."""
        if not validator.can_execute_command(command):
            return "Error: Command execution denied by policy."
            
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=workspace, 
                capture_output=True, 
                text=True,
                timeout=30 # Prevent hanging
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Command execution timed out after 30 seconds."
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def git_commit_and_push(message: str, branch_name: str) -> str:
        """Commits changes and pushes to a specific branch."""
        # Simple policy check: allow git tools implicitly if we have WRITE access
        if not validator.can_execute_command("git commit"): 
            return "Error: Git operations denied by policy."
            
        try:
            success = repo.commit_and_push(message, branch_name)
            return "Changes successfully committed and pushed." if success else "No changes to commit."
        except Exception as e:
            return f"Error with Git operation: {str(e)}"

    registry.register("read_file", "Read a file's content", read_file)
    registry.register("write_file", "Write content to a file", write_file)
    registry.register("execute_command", "Run a sandboxed shell command", execute_command)
    registry.register("git_commit_and_push", "Commit and push local changes", git_commit_and_push)
    
    return registry
