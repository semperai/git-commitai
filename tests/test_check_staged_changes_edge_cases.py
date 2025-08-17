from unittest.mock import patch
import git_commitai
import subprocess
from io import StringIO


class TestCheckStagedChangesEdgeCases:
    """Test edge cases in check_staged_changes."""

    def test_check_staged_changes_auto_stage_exception(self):
        """Test auto-stage with exception during git diff."""
        # The code actually catches the exception in a try block, so we need to mock run_git
        # to return a non-zero returncode instead of raising an exception
        with patch("subprocess.run") as mock_run:
            # First call for git diff --quiet should indicate there are changes
            mock_run.return_value.returncode = 1  # Non-zero means there are changes

            # Then the git add -u call should fail
            def side_effect(*args, **kwargs):
                if "diff" in args[0]:
                    result = subprocess.CompletedProcess(args, 1)
                    return result
                elif "add" in args[0]:
                    raise subprocess.CalledProcessError(1, args[0])
                return subprocess.CompletedProcess(args, 0)

            mock_run.side_effect = side_effect

            with patch("sys.stdout", new=StringIO()):
                result = git_commitai.check_staged_changes(auto_stage=True)
                assert result is False

    def test_check_staged_changes_amend_no_head(self):
        """Test amend when HEAD doesn't exist (initial commit)."""
        with patch("git_commitai.run_git", side_effect=subprocess.CalledProcessError(1, ["git"])):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                result = git_commitai.check_staged_changes(amend=True)
                assert result is False
                assert "nothing to amend" in fake_out.getvalue()

