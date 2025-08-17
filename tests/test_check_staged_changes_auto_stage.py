import subprocess
from unittest.mock import patch, MagicMock
from io import StringIO
import git_commitai

class TestCheckStagedChangesAutoStage:
    """Test auto-staging functionality in detail."""

    def test_check_staged_changes_auto_stage_subprocess_error(self):
        """Test auto-stage when subprocess.run fails."""
        with patch("subprocess.run") as mock_run:
            # First call checks for unstaged changes
            diff_result = MagicMock()
            diff_result.returncode = 1  # Has unstaged changes

            # Second call tries to stage files but fails
            mock_run.side_effect = [
                diff_result,
                subprocess.CalledProcessError(1, ["git", "add", "-u"])
            ]

            with patch("sys.stdout", new=StringIO()):
                result = git_commitai.check_staged_changes(auto_stage=True)
                assert result is False

