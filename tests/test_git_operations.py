import pytest
import subprocess
from unittest.mock import patch, MagicMock
import git_commitai

class TestGitOperations:
    """Test git-related operations."""

    def test_run_git_success(self):
        """Test successful git command execution."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "test output"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = git_commitai.run_git(["status"])
            assert result == "test output"

    def test_run_git_failure_with_check(self):
        """Test git command failure with check=True."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "status"])

            with pytest.raises(subprocess.CalledProcessError):
                git_commitai.run_git(["status"], check=True)

    def test_run_git_failure_without_check(self):
        """Test git command failure with check=False."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "status"])

            result = git_commitai.run_git(["status"], check=False)
            assert result == ""
