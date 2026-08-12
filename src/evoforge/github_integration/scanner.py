from pathlib import Path
from typing import Any


class RepositoryScanner:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def scan(self) -> dict[str, Any]:
        """Performs a basic static scan of the repository."""
        if not self.repo_path.exists():
            return {"error": "Repository path does not exist"}

        result = {
            "has_pyproject_toml": (self.repo_path / "pyproject.toml").exists(),
            "has_package_json": (self.repo_path / "package.json").exists(),
            "has_requirements_txt": (self.repo_path / "requirements.txt").exists(),
            "has_dockerfile": (self.repo_path / "Dockerfile").exists(),
            "has_github_workflows": (self.repo_path / ".github" / "workflows").exists(),
            "primary_language": self._detect_primary_language()
        }
        return result

    def _detect_primary_language(self) -> str:
        # Extremely basic heuristic
        if (self.repo_path / "pyproject.toml").exists() or (self.repo_path / "requirements.txt").exists():
            return "python"
        if (self.repo_path / "package.json").exists():
            return "javascript/typescript"
        if (self.repo_path / "Cargo.toml").exists():
            return "rust"
        if (self.repo_path / "go.mod").exists():
            return "go"
        
        return "unknown"
