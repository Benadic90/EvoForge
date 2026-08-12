import re

import structlog

logger = structlog.get_logger(__name__)

class ShellAllowlist:
    def __init__(self):
        # Extremely restrictive shell commands by default
        self.allowed_commands = [
            "ls", "pwd", "pytest", "python -m pytest", 
            "npm test", "npm run build", "yarn test", 
            "cargo test", "go test", "flake8", "ruff",
            "git status", "git diff", "git log"
        ]
        
        self.forbidden_patterns = [
            re.compile(r"rm\s+-rf\s+/"),
            re.compile(r">\s*/dev/sda"),
            re.compile(r"mkfs"),
            re.compile(r"wget\s+.*\s+\|\s*sh"),
            re.compile(r"curl\s+.*\s+\|\s*sh"),
            re.compile(r"chmod\s+-R\s+777"),
            re.compile(r"chown"),
            re.compile(r"su\s+"),
            re.compile(r"sudo\s+"),
        ]

    def is_allowed(self, command: str) -> bool:
        """Checks if a shell command is safe to execute autonomously."""
        
        # 1. Check forbidden patterns first (blocklist)
        for pattern in self.forbidden_patterns:
            if pattern.search(command):
                logger.warning("command_blocked_by_pattern", command=command, pattern=pattern.pattern)
                return False
                
        # 2. In strict mode, we might only allow exact matches from the allowlist
        # For MVP, we will do a soft allowlist (warn if not in allowlist, but if no forbidden pattern matches, maybe allow depending on strictness)
        # We will enforce strict allowlist for the base command.
        
        base_command = command.split()[0] if command else ""
        allowed_bases = ["python", "pytest", "npm", "yarn", "cargo", "go", "ruff", "git", "ls", "pwd", "echo", "cat", "grep"]
        
        if base_command not in allowed_bases:
            logger.warning("command_base_not_allowed", command=command, base=base_command)
            return False
            
        return True
