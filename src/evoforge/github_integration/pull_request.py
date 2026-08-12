import structlog
from typing import Optional
from .client import GitHubClient

logger = structlog.get_logger(__name__)

class PullRequestManager:
    def __init__(self, github_client: GitHubClient):
        self.client = github_client

    def create_pr(self, repo_full_name: str, title: str, body: str, head_branch: str, base_branch: str = "main") -> str:
        """Creates a Pull Request and returns its HTML URL."""
        repo = self.client.get_repo(repo_full_name)
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            logger.info("pull_request_created", url=pr.html_url)
            return pr.html_url
        except Exception as e:
            logger.error("pull_request_creation_failed", error=str(e))
            raise

    def get_pr_template(self, summary: str, motivation: str, changes: str, tasks_completed: dict) -> str:
        """Generates a standard PR description from a template."""
        
        agent_table = "| Step | Agent | Status |\n|------|-------|--------|\n"
        for task, (agent, status) in tasks_completed.items():
            agent_table += f"| {task} | {agent} | {status} |\n"
            
        return f"""## 🤖 EvoForge Automated PR

### Summary
{summary}

### Motivation
{motivation}

### Changes
{changes}

### Testing
- [x] Unit tests pass (if applicable)
- [x] Security scan clean

### Agent Workflow
{agent_table}

---
*This PR was created autonomously by EvoForge. Human review and approval is required before merge.*
"""
