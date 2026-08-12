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
