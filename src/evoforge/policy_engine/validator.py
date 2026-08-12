from pathlib import Path

import structlog

from evoforge.model_router.cost_tracker import CostTracker

from .permissions import PermissionLevel, RepositoryPolicy
from .secret_detector import SecretDetector
from .shell_allowlist import ShellAllowlist

logger = structlog.get_logger(__name__)

class ActionValidator:
    def __init__(self, policy: RepositoryPolicy, cost_tracker: CostTracker, dry_run: bool = False):
        self.policy = policy
        self.cost_tracker = cost_tracker
        self.shell_allowlist = ShellAllowlist()
        self.secret_detector = SecretDetector()
        self.dry_run = dry_run

    def can_read_file(self, file_path: str) -> bool:
        """Validates if the agent can read a specific file."""
        # Check against forbidden files
        path_obj = Path(file_path)
        for forbidden in self.policy.forbidden_files:
            if path_obj.match(forbidden) or str(path_obj.name) == forbidden:
                logger.warning("read_access_denied", file=file_path, reason="forbidden_file")
                return False
        return True

    def can_write_file(self, file_path: str, content: str) -> bool:
        """Validates if the agent can write to a specific file with given content."""
        if self.dry_run:
            logger.info("write_access_denied", file=file_path, reason="dry_run_enabled")
            return False
            
        if self.policy.level == PermissionLevel.READ_ONLY:
            logger.warning("write_access_denied", file=file_path, reason="read_only_policy")
            return False
            
        if not self.can_read_file(file_path): # If you can't read it, you can't write it
            return False

        # Scan content for secrets before allowing write
        secrets = self.secret_detector.scan_text(content)
        if secrets:
            logger.error("write_blocked_secrets_detected", file=file_path, secrets=[s[0] for s in secrets])
            return False
            
        return True

    def can_execute_command(self, command: str) -> bool:
        """Validates if a shell command is allowed."""
        if self.dry_run:
            logger.info("execution_denied", command=command, reason="dry_run_enabled")
            return False
            
        if self.policy.level in [PermissionLevel.READ_ONLY, PermissionLevel.READ_WRITE_CODE]:
            logger.warning("execution_denied", command=command, reason="insufficient_permissions")
            return False
            
        # Admin can run anything (use with extreme caution)
        if self.policy.level == PermissionLevel.ADMIN:
            return True
            
        # Sandbox execution
        return self.shell_allowlist.is_allowed(command)
        
    def can_use_budget(self, estimated_cost: float) -> bool:
        """Validates if the action fits within the repository's budget."""
        # Basic check, in reality we'd check the project-specific spend vs max_budget_usd
        project_spent = self.cost_tracker.per_project_spent.get(self.policy.repo_name, 0.0)
        if project_spent + estimated_cost > self.policy.max_budget_usd:
            logger.warning("budget_limit_reached", repo=self.policy.repo_name)
            return False
        return self.cost_tracker.can_afford(estimated_cost)
