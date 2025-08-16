"""Tests for -n/--no-verify hook skipping functionality."""

import tempfile
from unittest.mock import patch

import git_commitai


class TestNoVerifyFlag:
    """Test the -n/--no-verify hook skipping functionality."""

    def test_commit_with_no_verify_flag(self):
        """Test that --no-verify flag is passed to git commit."""
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
                                                with patch("sys.argv", ["git-commitai", "-n"]):
                                                    git_commitai.main()

                                                    # Find the git commit call
                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    assert len(commit_calls) > 0

                                                    # Verify --no-verify is in the command
                                                    last_commit_call = commit_calls[-1]
                                                    assert "--no-verify" in last_commit_call[0][0]

    def test_commit_with_short_no_verify_flag(self):
        """Test that -n flag works as shorthand for --no-verify."""
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
                                                # Test with -n shorthand
                                                with patch("sys.argv", ["git-commitai", "-n"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    last_commit_call = commit_calls[-1]
                                                    assert "--no-verify" in last_commit_call[0][0]

    def test_no_verify_with_amend(self):
        """Test that --no-verify works with --amend."""
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

                    with patch("git_commitai.make_api_request", return_value="Amended commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--amend", "-n"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    last_commit_call = commit_calls[-1]

                                                    # Should have both --amend and --no-verify
                                                    assert "--amend" in last_commit_call[0][0]
                                                    assert "--no-verify" in last_commit_call[0][0]

    def test_no_verify_with_auto_stage(self):
        """Test that --no-verify works with -a flag."""
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

                    with patch("git_commitai.make_api_request", return_value="Auto-staged commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-a", "-n"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    last_commit_call = commit_calls[-1]
                                                    assert "--no-verify" in last_commit_call[0][0]

    def test_create_commit_message_file_with_no_verify(self):
        """Test that commit message file notes when hooks will be skipped."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = "M\tfile1.txt"

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Test commit message",
                        amend=False,
                        auto_staged=False,
                        no_verify=True,
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Test commit message" in content
                    assert "# Git hooks will be skipped (--no-verify)." in content

    def test_prompt_includes_no_verify_note(self):
        """Test that the AI prompt mentions hook skipping when -n is used."""
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

                    with patch("git_commitai.make_api_request", return_value="Test") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-n"]):
                                                    git_commitai.main()

                                                    # Check that the prompt includes no-verify note
                                                    call_args = mock_api.call_args[0]
                                                    prompt = call_args[1]
                                                    assert "Git hooks will be skipped" in prompt
                                                    assert "--no-verify" in prompt

    def test_combined_flags(self):
        """Test combining multiple flags including --no-verify."""
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

                    with patch("git_commitai.make_api_request", return_value="Complex commit") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                # Combine -a, -n, and -m flags
                                                with patch("sys.argv", ["git-commitai", "-a", "-n", "-m", "quick fix"]):
                                                    git_commitai.main()

                                                    # Verify all flags are properly handled
                                                    # Check API prompt
                                                    call_args = mock_api.call_args[0]
                                                    prompt = call_args[1]
                                                    assert "quick fix" in prompt
                                                    assert "automatically staged" in prompt
                                                    assert "hooks will be skipped" in prompt

                                                    # Check create_commit_message_file call
                                                    create_args = mock_create.call_args[1]
                                                    assert create_args["auto_staged"]
                                                    assert create_args["no_verify"]

                                                    # Check git commit command
                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    if commit_calls:
                                                        last_commit_call = commit_calls[-1]
                                                        assert "--no-verify" in last_commit_call[0][0]

    def test_commit_without_no_verify(self):
        """Test that commits without -n flag don't include --no-verify."""
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

                    with patch("git_commitai.make_api_request", return_value="Normal commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai"]):
                                                    git_commitai.main()

                                                    # Verify --no-verify is NOT in the command
                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    if commit_calls:
                                                        last_commit_call = commit_calls[-1]
                                                        assert "--no-verify" not in last_commit_call[0][0]
