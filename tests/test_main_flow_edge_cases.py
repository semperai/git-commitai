import pytest
from io import StringIO
from unittest.mock import patch
import git_commitai

class TestMainFlowEdgeCases:
    """Test edge cases in main flow."""

    def test_main_help_with_man_page(self):
        """Test --help flag when man page is available."""
        with patch("sys.argv", ["git-commitai", "--help"]):
            with patch("git_commitai.show_man_page", return_value=True):
                with pytest.raises(SystemExit) as exc_info:
                    git_commitai.main()
                assert exc_info.value.code == 0

    def test_main_version_flag(self):
        """Test --version flag."""
        with patch("sys.argv", ["git-commitai", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    git_commitai.main()
                output = fake_out.getvalue()
                assert git_commitai.__version__ in output

    def test_main_debug_flag(self):
        """Test --debug flag enables debug mode."""
        with patch("sys.argv", ["git-commitai", "--debug"]):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                with patch("git_commitai.check_staged_changes", return_value=False):
                    with patch("git_commitai.show_git_status"):
                        with pytest.raises(SystemExit):
                            git_commitai.main()
                        assert git_commitai.DEBUG is True
        # Reset DEBUG flag
        git_commitai.DEBUG = False

    def test_main_strip_comments_failure(self):
        """Test main flow when strip_comments_and_save fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

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
                                            with patch("git_commitai.strip_comments_and_save", return_value=False):
                                                with pytest.raises(SystemExit) as exc_info:
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()
                                                assert exc_info.value.code == 1


