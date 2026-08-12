from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class PermissionLevel(Enum):
    READ_ONLY = "read_only"
    READ_WRITE_SANDBOX = "read_write_sandbox"
    READ_WRITE_CODE = "read_write_code"
    ADMIN = "admin"

class RepositoryPolicy(BaseModel):
    repo_name: str
    level: PermissionLevel
    allowed_branches: List[str] = ["*"]
    forbidden_files: List[str] = [".env", "secrets.json", "credentials.yml"]
    max_budget_usd: float = 1.0

# Example global default policy
DEFAULT_POLICY = RepositoryPolicy(
    repo_name="*",
    level=PermissionLevel.READ_WRITE_CODE,
    allowed_branches=["agent/*", "feature/*", "fix/*"],
    forbidden_files=[".env", ".npmrc", ".gitconfig", "*.key", "*.pem"],
    max_budget_usd=5.0
)
