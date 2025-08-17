import pytest
import subprocess
from unittest.mock import patch, MagicMock
import git_commitai

class TestMainFlowBoundaryConditions:
    """Test main flow with boundary conditions."""

    def test_main_with_git_commit_subprocess_error(self):
        """Test main when git commit raises subprocess error."""
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                # Allow initial git checks to pass
                if isinstance(args[0], list) and "commit" in args[0]:
                    raise subprocess.CalledProcessError(128, ["git", "commit"], stderr="fatal: error")
                result = MagicMock()
                result.returncode = 0
                return result

            mock_run.side_effect = side_effect

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                        "repo_config": {}
                    }

                    with patch("git_commitai.make_api_request", return_value="Test"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with pytest.raises(SystemExit) as exc_info:
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()
                                                assert exc_info.value.code == 128
