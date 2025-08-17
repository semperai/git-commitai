"""Tests for main flow and integration."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from io import StringIO

import git_commitai


class TestMainFlow:
    """Test the main flow of the application."""

    def test_not_in_git_repo(self):
        """Test behavior when not in a git repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")

            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    with patch("sys.argv", ["git-commitai"]):
                        git_commitai.main()

                assert exc_info.value.code == 128
                assert "fatal: not a git repository" in fake_out.getvalue()

    def test_successful_commit(self):
        """Test successful commit flow."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai"]):
                                                    git_commitai.main()

                                                    # Ensure git commit was invoked
                                                    calls = [c.args[0] for c in mock_run.call_args_list if c.args]
                                                    assert any(
                                                        isinstance(cmd, list) and "commit" in cmd
                                                        for cmd in calls
                                                    )

    def test_aborted_commit_no_save(self):
        """Test aborting commit by not saving the file."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                # Same mtime before and after - file not saved
                                with patch("os.path.getmtime", side_effect=[1000, 1000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("sys.stdout", new=StringIO()) as fake_out:
                                            with pytest.raises(SystemExit) as exc_info:
                                                with patch("sys.argv", ["git-commitai"]):
                                                    git_commitai.main()

                                            assert exc_info.value.code == 1
                                            assert "Aborting commit due to empty commit message" in fake_out.getvalue()

    def test_aborted_commit_empty_message(self):
        """Test aborting commit with empty message after save."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                # Different mtime - file was saved
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        # But message is empty
                                        with patch("git_commitai.is_commit_message_empty", return_value=True):
                                            with patch("sys.stdout", new=StringIO()) as fake_out:
                                                with pytest.raises(SystemExit) as exc_info:
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()

                                                assert exc_info.value.code == 1
                                                assert "Aborting commit due to empty commit message" in fake_out.getvalue()

    def test_commit_with_context_message(self):
        """Test commit with -m context message."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-m", "Added new feature"]):
                                                    git_commitai.main()

                                                    # Check that context was included in prompt
                                                    call_args = mock_api.call_args[0]
                                                    prompt = call_args[1]
                                                    assert "Added new feature" in prompt

    def test_git_commit_failure(self):
        """Test handling of git commit command failure."""
        with patch("subprocess.run") as mock_run:
            # First calls succeed, last one (git commit) fails
            def side_effect(*args, **kwargs):
                if "commit" in str(args):
                    raise subprocess.CalledProcessError(1, "git commit")
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with pytest.raises(SystemExit) as exc_info:
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()

                                                assert exc_info.value.code == 1
