import subprocess
from unittest.mock import patch
import git_commitai

class TestRunGitExceptionHandling:
    """Test run_git exception handling."""

    def test_run_git_with_check_false_no_stdout(self):
        """Test run_git with check=False when CalledProcessError has no stdout."""
        with patch("subprocess.run") as mock_run:
            error = subprocess.CalledProcessError(1, ["git", "status"])
            error.stdout = None
            error.output = None
            mock_run.side_effect = error

            result = git_commitai.run_git(["status"], check=False)
            assert result == ""
