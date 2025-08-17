import subprocess
from unittest.mock import MagicMock, patch
import git_commitai

class TestRunGitEdgeCases:
    """Test edge cases in run_git function."""

    def test_run_git_no_output(self):
        """Test run_git with no output."""
        with patch("git_commitai.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = git_commitai.run_git(["status"])
            assert result == ""
            mock_run.assert_called_once_with(
                ["git", "status"],
                capture_output=True,
                text=True,
                check=True,
            )


    def test_run_git_check_false_with_error(self):
        """Test run_git with check=False and error."""
        with patch("git_commitai.subprocess.run") as mock_run:
            error = subprocess.CalledProcessError(1, ["git", "status"], stderr="error")
            error.stdout = "some output"
            mock_run.side_effect = error

            # With check=False, should return stdout even on error
            result = git_commitai.run_git(["status"], check=False)
            assert result == "some output"
            _, kwargs = mock_run.call_args
            assert kwargs.get("check") is False

