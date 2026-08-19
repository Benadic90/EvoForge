import os
import json
import time
import shutil
import tempfile
import subprocess
import litellm
import structlog
from pathlib import Path

from evoforge.agents.contracts import AgentContext, AgentResult

logger = structlog.get_logger(__name__)

class ToolLoopRunner:
    def __init__(self, db, model_id: str, timeout_seconds: float = 300.0):
        self.db = db
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds

    def get_github_token(self):
        from evoforge.github_integration.client import GitHubClient
        client = GitHubClient(db=self.db)
        if client.token:
            return client.token
        return os.environ.get("GITHUB_TOKEN")

    def run(self, context: AgentContext, api_key: str) -> AgentResult:
        if not context.repository_id:
            return AgentResult(
                success=False,
                agent_id="tool_loop",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary="Missing repository_id for tool loop execution.",
                metrics={"failure_class": "missing_repository"},
            )

        repo_full_name = context.repository_id
        github_token = self.get_github_token()

        workspace = tempfile.mkdtemp(prefix="evoforge_agent_workspace_")
        
        try:
            # 1. Clone
            clone_cmd = ["git", "clone", "--depth", "1"]
            
            if os.path.isdir(repo_full_name):
                # Local repository for tests
                clone_url = repo_full_name
            else:
                if github_token:
                    clone_url = f"https://x-access-token:{github_token}@github.com/{repo_full_name}.git"
                else:
                    clone_url = f"https://github.com/{repo_full_name}.git"
            
            clone_cmd.extend([clone_url, workspace])
            logger.info("tool_loop_cloning", repo=repo_full_name)
            res = subprocess.run(clone_cmd, capture_output=True, text=True, check=False)
            if res.returncode != 0:
                return self._fail("git_clone_failed", res.stderr, context)

            # Create task branch
            clean_task_id = context.task_id.replace("task_", "").replace("-", "")[:8]
            branch_name = f"evoforge/patch-{clean_task_id}"
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=workspace, check=False)

            # 2. Tool definitions
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "shell_execute",
                        "description": "Execute a shell command as a list of arguments (e.g. ['pytest', 'tests/']). Does NOT use a shell, so no pipelines or interpolations.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Command list"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read contents of a file in the workspace.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string"}
                            },
                            "required": ["filepath"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Write contents to a file in the workspace.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["filepath", "content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "list_files",
                        "description": "List files in a directory within the workspace.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "directory": {"type": "string", "default": "."}
                            }
                        }
                    }
                }
            ]

            messages = [
                {
                    "role": "system",
                    "content": "You are a software engineer modifying a codebase. You have access to tools to read, write, list files, and run shell commands (like tests). You MUST run the repository's tests before finishing if you make changes."
                },
                {
                    "role": "user",
                    "content": f"Task: {context.task_description}\nRepository is cloned in your workspace. Start by exploring."
                }
            ]

            # 3. LLM Loop
            max_iterations = 15
            tests_run = []
            changed_files = set()
            tests_passed = None

            for i in range(max_iterations):
                response = litellm.completion(
                    model=self.model_id,
                    messages=messages,
                    api_key=api_key,
                    tools=tools,
                    timeout=self.timeout_seconds
                )
                
                msg = response.choices[0].message
                
                # We need to append the model's message exactly as it is for tool_calls tracking
                messages.append(msg.model_dump(exclude_unset=True))
                
                if not msg.tool_calls:
                    # Final answer
                    final_summary = msg.content or "No summary provided."
                    break

                for tc in msg.tool_calls:
                    func_name = tc.function.name
                    func_args = json.loads(tc.function.arguments)
                    result_str = ""

                    try:
                        if func_name == "shell_execute":
                            cmd = func_args.get("command", [])
                            if not isinstance(cmd, list):
                                result_str = "Error: command must be a list of strings."
                            else:
                                if "pytest" in cmd[0] or "test" in cmd[0] or "npm" in cmd[0] or "yarn" in cmd[0]:
                                    tests_run.append(" ".join(cmd))
                                    
                                proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=30)
                                if "pytest" in cmd[0] or "test" in cmd[0] or "npm" in cmd[0] or "yarn" in cmd[0]:
                                    tests_passed = (proc.returncode == 0)
                                    
                                result_str = f"Exit code: {proc.returncode}\nStdout: {proc.stdout[:2000]}\nStderr: {proc.stderr[:2000]}"
                                
                        elif func_name == "read_file":
                            fp = Path(workspace) / func_args["filepath"]
                            fp = fp.resolve()
                            if not str(fp).startswith(str(Path(workspace).resolve())):
                                result_str = "Error: path escapes workspace."
                            elif fp.exists() and fp.is_file():
                                with open(fp, "r", encoding="utf-8") as f:
                                    result_str = f.read()[:5000]
                            else:
                                result_str = "Error: File not found."
                                
                        elif func_name == "write_file":
                            fp = Path(workspace) / func_args["filepath"]
                            fp = fp.resolve()
                            if not str(fp).startswith(str(Path(workspace).resolve())):
                                result_str = "Error: path escapes workspace."
                            else:
                                fp.parent.mkdir(parents=True, exist_ok=True)
                                with open(fp, "w", encoding="utf-8") as f:
                                    f.write(func_args["content"])
                                changed_files.add(func_args["filepath"])
                                result_str = "File written successfully."
                                
                        elif func_name == "list_files":
                            d = func_args.get("directory", ".")
                            dp = Path(workspace) / d
                            dp = dp.resolve()
                            if not str(dp).startswith(str(Path(workspace).resolve())):
                                result_str = "Error: path escapes workspace."
                            elif dp.exists() and dp.is_dir():
                                files = os.listdir(dp)
                                result_str = "\n".join(files)
                            else:
                                result_str = "Error: Directory not found."
                        else:
                            result_str = f"Error: unknown tool {func_name}"
                            
                    except Exception as e:
                        result_str = f"Exception during execution: {e!s}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": func_name,
                        "content": result_str
                    })

            # Check Git Diff
            status_res = subprocess.run(["git", "status", "--porcelain"], cwd=workspace, capture_output=True, text=True)
            git_status = status_res.stdout.strip()
            
            commit_required = bool(git_status)

            return AgentResult(
                success=True,
                agent_id="tool_loop",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=final_summary if 'final_summary' in locals() else "Max iterations reached.",
                changed_files=list(changed_files),
                tests_run=tests_run,
                tests_passed=tests_passed,
                git_status=git_status,
                workspace=workspace,
                commit_required=commit_required
            )
            
        except Exception as e:
            return self._fail("tool_loop_exception", str(e), context)

    def _fail(self, code: str, msg: str, context: AgentContext) -> AgentResult:
        logger.error(code, error=msg)
        return AgentResult(
            success=False,
            agent_id="tool_loop",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary=msg,
            errors=[msg],
            metrics={
                "failure_class": code,
                "latency_ms": 1.0,
            }
        )
