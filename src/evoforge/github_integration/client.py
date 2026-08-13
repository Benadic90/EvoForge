import os

import structlog
from github import Github
from github.GithubException import GithubException

logger = structlog.get_logger(__name__)

class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            logger.warning("github_token_missing")
            self.client = Github() # Unauthenticated (highly rate limited)
        else:
            self.client = Github(self.token)
            
    def get_user_repositories(self) -> list[str]:
        """Fetch all repositories owned by the authenticated user."""
        try:
            user = self.client.get_user()
            repos = [repo.full_name for repo in user.get_repos(affiliation="owner")]
            logger.info("repositories_discovered", count=len(repos))
            return repos
        except GithubException as e:
            logger.error("repository_discovery_failed", error=str(e))
            raise

    def get_repo(self, full_name: str):
        """Get a repository by full name (e.g. user/repo)."""
        try:
            return self.client.get_repo(full_name)
        except GithubException as e:
            logger.error("get_repo_failed", repo=full_name, error=str(e))
            raise

    def get_open_issues(self, repo_full_name: str, limit: int = 50) -> list[dict]:
        try:
            repo = self.get_repo(repo_full_name)
            # Fetch issues that are NOT pull requests
            issues = []
            for issue in repo.get_issues(state='open'):
                if issue.pull_request is None:
                    issues.append({
                        "id": str(issue.number),
                        "title": issue.title,
                        "body": issue.body,
                        "created_at": issue.created_at,
                        "labels": [lbl.name for lbl in issue.labels]
                    })
                    if len(issues) >= limit:
                        break
            return issues
        except GithubException as e:
            logger.error("get_open_issues_failed", repo=repo_full_name, error=str(e))
            return []

    def get_open_prs(self, repo_full_name: str, limit: int = 50) -> list[dict]:
        try:
            repo = self.get_repo(repo_full_name)
            prs = []
            for pr in repo.get_pulls(state='open'):
                prs.append({
                    "id": str(pr.number),
                    "title": pr.title,
                    "created_at": pr.created_at
                })
                if len(prs) >= limit:
                    break
            return prs
        except GithubException as e:
            logger.error("get_open_prs_failed", repo=repo_full_name, error=str(e))
            return []

    def get_recent_commits(self, repo_full_name: str, limit: int = 10) -> list[dict]:
        try:
            repo = self.get_repo(repo_full_name)
            commits = []
            for commit in repo.get_commits():
                commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "date": commit.commit.author.date
                })
                if len(commits) >= limit:
                    break
            return commits
        except GithubException as e:
            logger.error("get_recent_commits_failed", repo=repo_full_name, error=str(e))
            return []

    def get_ci_state(self, repo_full_name: str, ref: str = "main") -> str:
        try:
            repo = self.get_repo(repo_full_name)
            commits = repo.get_commits(sha=ref)
            if commits.totalCount > 0:
                last_commit = commits[0]
                status = last_commit.get_combined_status()
                return status.state  # 'failure', 'pending', 'success'
            return "unknown"
        except GithubException as e:
            logger.error("get_ci_state_failed", repo=repo_full_name, error=str(e))
            return "unknown"
