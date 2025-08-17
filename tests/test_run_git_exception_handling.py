import subprocess
from unittest.mock import patch
import git_commitai

class TestRunGitExceptionHandling:
    """Test run_git exception handling."""

    def test_run_git_with_check_false_no_stdout(self):
        """Test run_git with check=False when CalledProcessError has no stdout."""
        with patch("git_commitai.subprocess.run") as mock_run:
            error = subprocess.CalledProcessError(1, ["git", "status"])
            error.stdout = None
            error.output = None
            mock_run.side_effect = error

            result = git_commitai.run_git(["status"], check=False)
            assert result == ""
            # Ensure run_git invoked subprocess with check=False
            _, kwargs = mock_run.call_args
            assert kwargs.get("check") is False

