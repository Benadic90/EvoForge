import pytest
from unittest.mock import patch, MagicMock
from evoforge.github_integration.client import GitHubClient
from evoforge.github_integration.scanner import RepositoryScanner
import tempfile
import os

@patch('evoforge.github_integration.client.Github')
def test_github_client_init(mock_github):
    client = GitHubClient(token="fake_token")
    mock_github.assert_called_with("fake_token")

def test_repository_scanner():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create fake pyproject.toml
        with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
            f.write("")
            
        scanner = RepositoryScanner(temp_dir)
        results = scanner.scan()
        
        assert results["has_pyproject_toml"] is True
        assert results["has_package_json"] is False
        assert results["primary_language"] == "python"
