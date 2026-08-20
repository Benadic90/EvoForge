import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime

import structlog

from evoforge.github_integration.client import GitHubClient
from evoforge.github_integration.pull_request import PullRequestManager
from evoforge.memory.database import Database

logger = structlog.get_logger(__name__)


class AutonomousGitWorkflow:
    """Manages the full Git lifecycle: cloning, branching, committing, pushing, and opening GitHub PRs."""

    def __init__(self, db: Database | None = None, token: str | None = None):
        self.db = db
        self.client = GitHubClient(token=token, db=db)
        self.pr_manager = PullRequestManager(self.client)

    def publish_task_solution(
        self,
        repo_full_name: str,
        task_id: str,
        task_title: str,
        task_description: str,
        solution_summary: str,
        file_changes: dict[str, str] | None = None,
        agent_result=None,
    ) -> str | None:
        """
        Consumes a validated workspace diff or legacy fallback.
        """
        token = self.client.token
        
        # If AgentResult has workspace and no commit is required (e.g. no changes)
        if agent_result and agent_result.workspace and not agent_result.commit_required:
            logger.info("no_changes_required_skipping_git_push", repo=repo_full_name, task_id=task_id)
            return "NO_CHANGES_REQUIRED"
            
        if solution_summary == "NO_CHANGES_REQUIRED" or (not solution_summary and not file_changes and not agent_result):
            logger.info("no_changes_required_skipping_git_push", repo=repo_full_name, task_id=task_id)
            return "NO_CHANGES_REQUIRED"

        if not token:
            logger.warning("git_publish_skipped_no_token", repo=repo_full_name, task_id=task_id)
            return None

        clean_task_id = task_id.replace("task_", "").replace("-", "")[:8]
        branch_name = f"evoforge/patch-{clean_task_id}"

        try:
            if agent_result and agent_result.workspace:
                # 1. Use the agent's pre-populated workspace
                temp_dir = agent_result.workspace
                
                # Check for Markdown-only fake success
                status_res = subprocess.run(["git", "status", "--porcelain"], cwd=temp_dir, capture_output=True, text=True, check=False)
                git_lines = status_res.stdout.strip().split("\n")
                if len(git_lines) == 1 and ".evoforge_task_" in git_lines[0]:
                    logger.warning("fake_markdown_change", task_id=task_id)
                if not status_res.stdout.strip():
                    logger.warning("no_files_changed", task_id=task_id)

                # Force PR creation anyway so we can debug Llama 70B's textual output
                # (We will push an empty commit)
                subprocess.run(["git", "commit", "--allow-empty", "-m", f"chore: force empty commit for debugging {task_id}"], cwd=temp_dir, check=False)
                
                # If test execution failed, we DO NOT commit
                if agent_result.tests_run and agent_result.tests_passed is False:
                    logger.warning("tests_failed_skipping_commit", task_id=task_id)
                    return "TESTS_FAILED"
            else:
                # Legacy path (for fallback/textual answers)
                temp_dir = tempfile.mkdtemp(prefix="evoforge_git_")
                clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
                logger.info("cloning_repository", repo=repo_full_name, branch=branch_name)

                clone_res = subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, temp_dir],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if clone_res.returncode != 0:
                    logger.error("git_clone_failed", error=clone_res.stderr)
                    return None

                subprocess.run(["git", "checkout", "-b", branch_name], cwd=temp_dir, check=False)

                if file_changes:
                    for file_path, content in file_changes.items():
                        full_path = os.path.join(temp_dir, file_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(content)
                
                subprocess.run(["git", "commit", "--allow-empty", "-m", f"chore: force empty commit for debugging {task_id}"], cwd=temp_dir, check=False)

            # 2. Configure Git user
            subprocess.run(["git", "config", "user.name", "EvoForge Autonomous Agent"], cwd=temp_dir, check=False)
            subprocess.run(["git", "config", "user.email", "agent@evoforge.ai"], cwd=temp_dir, check=False)

            # 5. Stage & commit
            subprocess.run(["git", "add", "."], cwd=temp_dir, check=False)
            status_res = subprocess.run(["git", "status", "--porcelain"], cwd=temp_dir, capture_output=True, text=True, check=False)
            if not status_res.stdout.strip():
                logger.info("working_tree_clean", repo=repo_full_name)
                # Force commit to ensure PR is created
                subprocess.run(["git", "commit", "--allow-empty", "-m", "chore: force empty commit"], cwd=temp_dir, check=False)

            commit_msg = f"feat(evoforge): {task_title}\n\nAutomated implementation by EvoForge Developer Agent for task {task_id}."
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=temp_dir, check=False)

            # 6. Push to remote
            logger.info("pushing_git_branch", branch=branch_name, repo=repo_full_name)
            push_res = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if push_res.returncode != 0:
                logger.error("git_push_failed", error=push_res.stderr)
                return None

            # 7. Create GitHub Pull Request
            pr_body = self.pr_manager.get_pr_template(
                summary=f"Automated resolution for task `{task_title}`.",
                motivation=task_description,
                changes="\n".join([f"- Modified/Added `{ch}`" for ch in applied_changes]) + f"\n\n### Developer Agent Output\n```\n{solution_summary[:1000]}\n```",
                tasks_completed={task_title: ("DeveloperAgent", "Completed")}
            )

            pr_url = self.pr_manager.create_pr(
                repo_full_name=repo_full_name,
                title=f"🤖 EvoForge: {task_title}",
                body=pr_body,
                head_branch=branch_name,
                base_branch="main"
            )
            logger.info("autonomous_pr_published", repo=repo_full_name, pr_url=pr_url)
            return pr_url

        except Exception as e:
            logger.error("git_workflow_failed", error=str(e))
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
