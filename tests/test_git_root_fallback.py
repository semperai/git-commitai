import subprocess
from unittest.mock import patch
import git_commitai

class TestGitRootFallback:
    """Test git root directory fallback."""

    def test_get_git_root_exception_fallback(self):
        """Test get_git_root falls back to cwd on exception."""
        with patch("git_commitai.run_git", side_effect=Exception("Git error")):
            with patch("os.getcwd", return_value="/current/directory"):
                result = git_commitai.get_git_root()
                assert result == "/current/directory"

    def test_get_git_root_subprocess_error_fallback(self):
        """Test get_git_root falls back to cwd on CalledProcessError."""
        with patch("git_commitai.run_git", side_effect=subprocess.CalledProcessError(1, ["git"])):
            with patch("os.getcwd", return_value="/fallback/dir"):
                result = git_commitai.get_git_root()
                assert result == "/fallback/dir"

