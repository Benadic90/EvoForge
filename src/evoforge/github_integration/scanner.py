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
            "primary_language": self._detect_primary_language(),
            "has_tests": self._has_tests(),
            "has_docs": (self.repo_path / "README.md").exists() or (self.repo_path / "docs").exists(),
            "todo_count": self._count_todos()
        }
        return result
        
    def _has_tests(self) -> bool:
        return (self.repo_path / "tests").exists() or (self.repo_path / "test").exists() or (self.repo_path / "spec").exists()
        
    def _count_todos(self) -> int:
        import os
        count = 0
        try:
            for root, dirs, files in os.walk(self.repo_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                if 'node_modules' in dirs:
                    dirs.remove('node_modules')
                if 'venv' in dirs:
                    dirs.remove('venv')
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.md', '.txt', '.go', '.rs')):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                content = f.read()
                                count += content.upper().count('TODO') + content.upper().count('FIXME')
                        except Exception:
                            pass
        except Exception:
            pass
        return count

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
