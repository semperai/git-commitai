from io import StringIO
from unittest.mock import patch
import git_commitai

class TestShowGitStatusEdgeCases:
    """Test edge cases in show_git_status."""

    def test_show_git_status_exception_handling(self):
        """Test show_git_status with exceptions."""
        with patch("git_commitai.run_git", side_effect=Exception("Git error")):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()
                # Should show fallback message
                assert "On branch master" in output or "No changes" in output

    def test_show_git_status_empty_porcelain(self):
        """Test show_git_status with empty porcelain output."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.side_effect = [
                "main",  # branch name
                "",      # rev-parse HEAD (success)
                ""       # empty porcelain
            ]
            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()
                assert "nothing to commit, working tree clean" in output

