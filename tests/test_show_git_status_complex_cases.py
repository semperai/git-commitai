from io import StringIO
from unittest.mock import patch
import git_commitai

class TestShowGitStatusComplexCases:
    """Test complex cases in show_git_status."""

    def test_show_git_status_detached_head(self):
        """Test show_git_status in detached HEAD state."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "--show-current" in args:
                    return ""  # Empty means detached
                elif "rev-parse" in args and "--short" in args and "HEAD" in args:
                    return "abc1234"
                elif "rev-parse" in args and "HEAD" in args:
                    return "abc1234567890"  # Full SHA
                elif "--porcelain" in args:
                    return ""
                return ""

            mock_run.side_effect = side_effect

            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()
                assert "HEAD detached at abc1234" in output

    def test_show_git_status_all_exceptions(self):
        """Test show_git_status when all git commands fail."""
        with patch("git_commitai.run_git", side_effect=Exception("Git completely broken")):
            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()
                # Should show some fallback status
                assert "On branch master" in output or "No changes" in output

