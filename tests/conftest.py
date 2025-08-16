"""Shared fixtures and test configuration for git-commitai tests."""

import pytest
import os
import sys
from unittest.mock import patch

# Add parent directory to path so we can import git_commitai
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_env_config():
    """Fixture for mocking environment configuration."""
    with patch("git_commitai.get_env_config") as mock_config:
        mock_config.return_value = {
            "api_key": "test-key",
            "api_url": "http://test-api.com",
            "model": "test-model",
        }
        yield mock_config


@pytest.fixture
def mock_git_repo():
    """Fixture for mocking a git repository."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run


@pytest.fixture
def mock_staged_changes():
    """Fixture for mocking staged changes check."""
    with patch("git_commitai.check_staged_changes", return_value=True) as mock_check:
        yield mock_check


@pytest.fixture
def mock_editor_flow():
    """Fixture for mocking the editor flow."""
    with patch("os.path.getmtime", side_effect=[1000, 2000]), \
         patch("git_commitai.open_editor"), \
         patch("git_commitai.is_commit_message_empty", return_value=False):
        yield


@pytest.fixture
def temp_git_dir(tmp_path):
    """Fixture for creating a temporary git directory."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return str(git_dir)
