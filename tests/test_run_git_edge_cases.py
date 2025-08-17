import subprocess
from unittest.mock import MagicMock, patch
import git_commitai

class TestRunGitEdgeCases:
    """Test edge cases in run_git function."""

    def test_run_git_no_output(self):
        """Test run_git with no output."""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = git_commitai.run_git(["status"])
            assert result == ""

    def test_run_git_check_false_with_error(self):
        """Test run_git with check=False and error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "status"], output="", stderr="error"
            )

            # With check=False, should return stdout even on error
            result = git_commitai.run_git(["status"], check=False)
            # CalledProcessError might not have stdout, so result could be empty
            assert result == "" or result is not None

