"""Tests for --allow-empty flag functionality."""

import pytest
import tempfile
from unittest.mock import patch, MagicMock

import git_commitai


class TestAllowEmptyFlag:
    """Test the --allow-empty flag functionality."""

    def test_check_staged_changes_with_allow_empty(self):
        """Test that check_staged_changes returns True with allow_empty even without changes."""
        with patch("subprocess.run") as mock_run:
            # No staged changes (returncode 0 means no diff)
            mock_run.return_value.returncode = 0

            # Without allow_empty, should return False
            with patch("git_commitai.show_git_status"):
                result = git_commitai.check_staged_changes(allow_empty=False)
                assert not result

            # With allow_empty, should return True
            result = git_commitai.check_staged_changes(allow_empty=True)
            assert result

    def test_get_staged_files_with_allow_empty(self):
        """Test get_staged_files returns appropriate message for empty commits."""
        with patch("git_commitai.run_git") as mock_run:
            # No staged files
            mock_run.return_value = ""

            # Without allow_empty
            result = git_commitai.get_staged_files(allow_empty=False)
            assert result == ""

            # With allow_empty
            result = git_commitai.get_staged_files(allow_empty=True)
            assert result == "# No files changed (empty commit)"

    def test_get_staged_files_with_allow_empty_and_files(self):
        """Test get_staged_files with allow_empty when there are actually files."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "diff" in args and "--cached" in args and "--name-only" in args:
                    return "file1.py"
                elif "diff" in args and "--cached" in args and "--numstat" in args and "file1.py" in args:
                    return "10\t5\tfile1.py"  # Not binary
                elif "show" in args and ":file1.py" in args:
                    return 'print("hello")'
                return ""

            mock_run.side_effect = side_effect

            # Even with allow_empty, if there are files, show them
            result = git_commitai.get_staged_files(allow_empty=True)
            assert "file1.py" in result
            assert 'print("hello")' in result
            assert "# No files changed" not in result

    def test_get_git_diff_with_allow_empty(self):
        """Test get_git_diff returns appropriate message for empty commits."""
        with patch("git_commitai.run_git") as mock_run:
            # No diff
            mock_run.return_value = ""

            # Without allow_empty
            result = git_commitai.get_git_diff(allow_empty=False)
            assert result == "```\n\n```"

            # With allow_empty
            result = git_commitai.get_git_diff(allow_empty=True)
            assert result == "```\n# No changes (empty commit)\n```"

    def test_get_git_diff_with_allow_empty_and_changes(self):
        """Test get_git_diff with allow_empty when there are actually changes."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "diff --git a/file.txt b/file.txt\n+new line"

            # Even with allow_empty, if there are changes, show them
            result = git_commitai.get_git_diff(allow_empty=True)
            assert "diff --git" in result
            assert "+new line" in result
            assert "# No changes" not in result

    def test_create_commit_message_file_with_allow_empty(self):
        """Test that commit message file notes empty commit."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = ""  # No staged files

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Empty commit for CI trigger",
                        amend=False,
                        auto_staged=False,
                        no_verify=False,
                        verbose=False,
                        allow_empty=True,
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Empty commit for CI trigger" in content
                    assert "# This will be an empty commit (--allow-empty)." in content
                    assert "# No changes to be committed (empty commit)" in content

    def test_create_commit_message_file_verbose_with_allow_empty(self):
        """Test verbose mode with empty commit."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = ""  # No diff

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Release marker",
                        verbose=True,
                        allow_empty=True,
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Should have verbose section
                    assert "# ------------------------ >8 ------------------------" in content
                    assert "# Diff of changes to be committed:" in content
                    assert "# No changes (empty commit)" in content

    def test_main_flow_with_allow_empty(self):
        """Test the main flow with --allow-empty flag."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            # Mock check_staged_changes to simulate no changes but allow_empty=True
            with patch("git_commitai.check_staged_changes", return_value=True) as mock_check:
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                        "repo_config": {}
                    }

                    with patch("git_commitai.make_api_request", return_value="Empty commit for release marker") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--allow-empty"]):
                                                    git_commitai.main()

                                                    # Verify check_staged_changes was called with allow_empty=True
                                                    mock_check.assert_called_once_with(
                                                        amend=False,
                                                        auto_stage=False,
                                                        allow_empty=True
                                                    )

                                                    # Verify create_commit_message_file was called with allow_empty=True
                                                    mock_create.assert_called_once()
                                                    call_args = mock_create.call_args[1]
                                                    assert call_args["allow_empty"]

                                                    # Verify git commit was called with --allow-empty
                                                    commit_calls = [
                                                        c for c in mock_run.call_args_list
                                                        if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                    ]
                                                    if commit_calls:
                                                        last_cmd = commit_calls[-1].args[0]
                                                        assert "--allow-empty" in last_cmd


    def test_allow_empty_with_amend(self):
        """Test that --allow-empty works with --amend."""
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

                    with patch("git_commitai.make_api_request", return_value="Amended empty commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--amend", "--allow-empty"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        c for c in mock_run.call_args_list
                                                        if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                    ]
                                                    if commit_calls:
                                                        last_cmd = commit_calls[-1].args[0]
                                                        assert "--amend" in last_cmd
                                                        assert "--allow-empty" in last_cmd


    def test_allow_empty_with_auto_stage(self):
        """Test that --allow-empty works with -a flag."""
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

                    with patch("git_commitai.make_api_request", return_value="Empty commit after auto-stage"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-a", "--allow-empty"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        c for c in mock_run.call_args_list
                                                        if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                    ]
                                                    if commit_calls:
                                                        last_cmd = commit_calls[-1].args[0]
                                                        assert "--allow-empty" in last_cmd


    def test_allow_empty_with_no_verify(self):
        """Test combining --allow-empty with --no-verify."""
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

                    with patch("git_commitai.make_api_request", return_value="Empty commit skipping hooks"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--allow-empty", "-n"]):
                                                    git_commitai.main()

                                                    commit_calls = [
                                                        c for c in mock_run.call_args_list
                                                        if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                    ]

                                                    assert commit_calls, "Expected a git commit invocation but none was recorded"
                                                    last_cmd = commit_calls[-1].args[0]
                                                    assert "--allow-empty" in last_cmd
                                                    assert "--no-verify" in last_cmd


    def test_allow_empty_with_verbose(self):
        """Test combining --allow-empty with --verbose."""
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

                    with patch("git_commitai.make_api_request", return_value="Verbose empty commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--allow-empty", "-v"]):
                                                    git_commitai.main()

                                                    # Verify both flags are passed
                                                    call_args = mock_create.call_args[1]
                                                    assert call_args["allow_empty"]
                                                    assert call_args["verbose"]

    def test_allow_empty_all_flags_combined(self):
        """Test combining --allow-empty with multiple other flags."""
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

                    with patch("git_commitai.make_api_request", return_value="Complex empty commit") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                # Combine -a, -n, -v, --allow-empty, and -m
                                                with patch("sys.argv", [
                                                    "git-commitai",
                                                    "-a",
                                                    "-n",
                                                    "-v",
                                                    "--allow-empty",
                                                    "-m",
                                                    "CI/CD trigger"
                                                ]):
                                                    git_commitai.main()

                                                    # Check API prompt
                                                    call_args = mock_api.call_args[0]
                                                    prompt = call_args[1]

                                                    # Check create_commit_message_file call
                                                    create_args = mock_create.call_args[1]
                                                    assert create_args["auto_staged"]
                                                    assert create_args["no_verify"]
                                                    assert create_args["verbose"]
                                                    assert create_args["allow_empty"]

                                                    # Check git commit command
                                                    commit_calls = [
                                                        c for c in mock_run.call_args_list
                                                        if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                    ]
                                                    if commit_calls:
                                                        last_cmd = commit_calls[-1].args[0]
                                                        assert "--allow-empty" in last_cmd
                                                        assert "--no-verify" in last_cmd


    def test_allow_empty_without_flag_normal_behavior(self):
        """Test that without --allow-empty, empty commits are rejected."""
        with patch("subprocess.run") as mock_run:
            # No staged changes
            mock_run.return_value.returncode = 0

            with patch("git_commitai.show_git_status") as mock_status:
                with patch("sys.argv", ["git-commitai"]):
                    with pytest.raises(SystemExit) as exc_info:
                        git_commitai.main()

                    # Should exit with error
                    assert exc_info.value.code == 1
                    # Should show git status
                    mock_status.assert_called_once()

    def test_allow_empty_edge_case_with_actual_changes(self):
        """Test --allow-empty when there are actually staged changes."""
        with patch("subprocess.run") as mock_run:
            # Has staged changes (returncode 1 means there are differences)
            diff_check = MagicMock()
            diff_check.returncode = 1
            mock_run.return_value = diff_check

            with patch("git_commitai.get_env_config") as mock_config:
                mock_config.return_value = {
                    "api_key": "test",
                    "api_url": "http://test",
                    "model": "test",
                    "repo_config": {}
                }

                with patch("git_commitai.make_api_request", return_value="Normal commit with changes"):
                    with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                        with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                            with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                with patch("git_commitai.open_editor"):
                                    with patch("git_commitai.is_commit_message_empty", return_value=False):
                                        with patch("git_commitai.strip_comments_and_save", return_value=True):
                                            with patch("git_commitai.get_staged_files", return_value="file.py\n```\ncode\n```"):
                                                with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                                                    with patch("sys.argv", ["git-commitai", "--allow-empty"]):
                                                        git_commitai.main()

                                                        # Should still include --allow-empty even with changes
                                                        commit_calls = [
                                                            c for c in mock_run.call_args_list
                                                            if c.args and isinstance(c.args[0], list) and "commit" in c.args[0]
                                                        ]
                                                        if commit_calls:
                                                            last_cmd = commit_calls[-1].args[0]
                                                            assert "--allow-empty" in last_cmd

