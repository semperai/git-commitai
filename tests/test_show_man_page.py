import subprocess
from unittest.mock import patch
import git_commitai

class TestShowManPage:
    """Test man page display functionality."""

    def test_show_man_page_success(self):
        """Test successful man page display."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = git_commitai.show_man_page()
            assert result is True
            mock_run.assert_called_once_with(["man", "git-commitai"], check=False)

    def test_show_man_page_failure(self):
        """Test man page display failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = git_commitai.show_man_page()
            assert result is False

    def test_show_man_page_exception(self):
        """Test man page display with exception."""
        with patch("subprocess.run", side_effect=FileNotFoundError("man not found")):
            result = git_commitai.show_man_page()
            assert result is False

    def test_show_man_page_subprocess_error(self):
        """Test man page display with CalledProcessError."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["man"])):
            result = git_commitai.show_man_page()
            assert result is False

