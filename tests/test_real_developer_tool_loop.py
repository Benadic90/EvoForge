import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
from evoforge.agents.contracts import AgentContext
from evoforge.memory.state import WorkflowStage
from evoforge.model_router.tool_loop import ToolLoopRunner

def test_real_developer_tool_loop():
    # 1. Create a dummy repository
    repo_dir = tempfile.mkdtemp(prefix="test_repo_")
    try:
        subprocess.run(["git", "init"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)

        # Setup repo files
        with open(os.path.join(repo_dir, "README.md"), "w") as f:
            f.write("# Test Repo")
        os.makedirs(os.path.join(repo_dir, "src"), exist_ok=True)
        with open(os.path.join(repo_dir, "src", "example.py"), "w") as f:
            f.write("def hello(): return 'hello'")
        os.makedirs(os.path.join(repo_dir, "tests"), exist_ok=True)
        with open(os.path.join(repo_dir, "tests", "test_example.py"), "w") as f:
            f.write("from src.example import hello\ndef test_hello(): assert hello() == 'hello'")

        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_dir, check=True)

        context = AgentContext(
            run_id="run_1",
            workflow_id="wf_1",
            task_id="task_1",
            task_description="Add a safe function and corresponding regression test.",
            project_id="proj_1",
            repository_id=repo_dir,  # Will clone from this local path in test
            current_stage=WorkflowStage.IMPLEMENT
        )

        # Create function mocks properly
        func1 = MagicMock()
        func1.name = "write_file"
        func1.arguments = '{"filepath": "src/example.py", "content": "def hello(): return \'hello\'\\ndef new_func(): return 1"}'
        
        call1 = MagicMock()
        call1.id = "call_1"
        call1.function = func1
        
        func2 = MagicMock()
        func2.name = "write_file"
        func2.arguments = '{"filepath": "tests/test_example.py", "content": "from src.example import hello, new_func\\ndef test_hello(): assert hello() == \'hello\'\\ndef test_new(): assert new_func() == 1"}'
        
        call2 = MagicMock()
        call2.id = "call_2"
        call2.function = func2
        
        func3 = MagicMock()
        func3.name = "shell_execute"
        func3.arguments = '{"command": ["pytest", "tests/"]}'
        
        call3 = MagicMock()
        call3.id = "call_3"
        call3.function = func3

        # Mock Litellm to simulate a tool loop
        responses = [
            # 1. LLM uses write_file to add a function
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=None,
                            tool_calls=[call1],
                            model_dump=lambda **kwargs: {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "write_file", "arguments": '{"filepath": "src/example.py", "content": "def hello(): return \'hello\'\\ndef new_func(): return 1"}'}}]}
                        )
                    )
                ]
            ),
            # 2. LLM uses write_file to add a test
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=None,
                            tool_calls=[call2],
                            model_dump=lambda **kwargs: {"role": "assistant", "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "write_file", "arguments": '{"filepath": "tests/test_example.py", "content": "from src.example import hello, new_func\\ndef test_hello(): assert hello() == \'hello\'\\ndef test_new(): assert new_func() == 1"}'}}]}
                        )
                    )
                ]
            ),
            # 3. LLM runs pytest
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=None,
                            tool_calls=[call3],
                            model_dump=lambda **kwargs: {"role": "assistant", "tool_calls": [{"id": "call_3", "type": "function", "function": {"name": "shell_execute", "arguments": '{"command": ["pytest", "tests/"]}'}}]}
                        )
                    )
                ]
            ),
            # 4. LLM returns final answer
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="I have added the function and the test, and verified they pass.",
                            tool_calls=None,
                            model_dump=lambda **kwargs: {"role": "assistant", "content": "I have added the function and the test, and verified they pass."}
                        )
                    )
                ]
            )
        ]

        with patch("litellm.completion", side_effect=responses):
            runner = ToolLoopRunner(db=None, model_id="test_model")
            
            # Monkeypatch the get_github_token so it uses the local path
            runner.get_github_token = lambda: None
            
            res = runner.run(context, api_key="dummy")

        assert res.success is True
        assert "tests_passed=True" or res.tests_passed is True
        assert res.commit_required is True
        assert len(res.changed_files) == 2
        
        # Verify the workspace actually changed
        with open(os.path.join(res.workspace, "src", "example.py")) as f:
            assert "new_func" in f.read()

    finally:
        def handle_remove_readonly(func, path, exc):
            import stat
            excvalue = exc[1]
            if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == 13:
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
                func(path)
            else:
                raise
        shutil.rmtree(repo_dir, onerror=handle_remove_readonly)
        if os.path.exists(res.workspace):
            shutil.rmtree(res.workspace, onerror=handle_remove_readonly)

