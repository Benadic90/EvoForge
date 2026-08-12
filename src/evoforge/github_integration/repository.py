from pathlib import Path

import structlog
from git import GitCommandError, Repo

logger = structlog.get_logger(__name__)

class LocalRepository:
    def __init__(self, workspace_dir: str, repo_full_name: str, clone_url: str):
        self.workspace_dir = Path(workspace_dir)
        self.repo_name = repo_full_name.replace("/", "_")
        self.repo_path = self.workspace_dir / self.repo_name
        self.clone_url = clone_url
        self.repo: Repo | None = None

    def clone_or_update(self):
        """Clones the repository if it doesn't exist, otherwise pulls latest."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                logger.info("updating_repository", path=str(self.repo_path))
                self.repo = Repo(self.repo_path)
                self.repo.remotes.origin.fetch()
                # Assuming main or master is the default branch. Would need to detect this dynamically in prod.
                current_branch = self.repo.active_branch.name
                if current_branch in ["main", "master"]:
                    self.repo.remotes.origin.pull()
            else:
                logger.info("cloning_repository", url=self.clone_url, path=str(self.repo_path))
                self.repo = Repo.clone_from(self.clone_url, self.repo_path)
        except GitCommandError as e:
            logger.error("git_operation_failed", error=str(e))
            raise

    def create_branch(self, branch_name: str, base_branch: str = "main", dry_run: bool = False):
        """Creates and checks out a new branch from a base branch."""
        if dry_run:
            logger.info("dry_run_create_branch", branch=branch_name)
            return
            
        if not self.repo:
            raise ValueError("Repository not initialized. Call clone_or_update() first.")
            
        try:
            # Ensure we are on the base branch and up to date
            self.repo.git.checkout(base_branch)
            self.repo.remotes.origin.pull(base_branch)
            
            # Check if branch exists
            if branch_name in self.repo.heads:
                logger.info("branch_already_exists", branch=branch_name)
                self.repo.heads[branch_name].checkout()
                return

            # Create and checkout new branch
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            logger.info("branch_created", branch=branch_name)
        except GitCommandError as e:
            logger.error("create_branch_failed", branch=branch_name, error=str(e))
            raise

    def commit_and_push(self, message: str, branch_name: str, dry_run: bool = False):
        """Commits all tracked and untracked changes and pushes to remote."""
        if dry_run:
            logger.info("dry_run_commit_and_push", message=message, branch=branch_name)
            return True
            
        if not self.repo:
            raise ValueError("Repository not initialized.")
            
        try:
            self.repo.git.add(A=True)
            if not self.repo.is_dirty(untracked_files=True) and not self.repo.index.diff("HEAD"):
                logger.info("no_changes_to_commit")
                return False
                
            self.repo.index.commit(message)
            origin = self.repo.remotes.origin
            origin.push(refspec=f"{branch_name}:{branch_name}")
            logger.info("changes_pushed", branch=branch_name)
            return True
        except GitCommandError as e:
            logger.error("commit_push_failed", error=str(e))
            raise
