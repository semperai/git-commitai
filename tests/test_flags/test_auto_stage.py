"""Tests for -a/--all auto-stage flag functionality."""

import pytest
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO

import git_commitai


class TestAutoStageFlag:
    """Test the -a/--all auto-stage functionality."""

    def test_stage_all_tracked_files(self):
        """Test that stage_all_tracked_files calls git add -u."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = git_commitai.stage_all_tracked_files()

            assert result
            mock_run.assert_called_once_with(
                ["git", "add", "-u"], check=True, capture_output=True
            )

    def test_stage_all_tracked_files_error(self):
        """Test handling of errors when staging files."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git add -u")

            with patch("sys.stdout", new=StringIO()) as fake_out:
                result = git_commitai.stage_all_tracked_files()
                output = fake_out.getvalue()

                assert result == False
                assert "Error: Failed to stage tracked files" in output

    def test_check_staged_changes_with_auto_stage(self):
        """Test check_staged_changes with auto_stage=True."""
        with patch("subprocess.run") as mock_run:
            # First call: check for unstaged changes (git diff --quiet)
            # Returns non-zero if there are changes
            diff_check = MagicMock()
            diff_check.returncode = 1  # There are unstaged changes

            # Second call: stage files (git add -u)
            stage_result = MagicMock()
            stage_result.returncode = 0  # Success

            # Third call: check for staged changes (git diff --cached --quiet)
            staged_check = MagicMock()
            staged_check.returncode = 1  # There are staged changes

            mock_run.side_effect = [diff_check, stage_result, staged_check]

            result = git_commitai.check_staged_changes(auto_stage=True)

            assert result
            assert mock_run.call_count == 3

    def test_check_staged_changes_auto_stage_no_changes(self):
        """Test auto_stage when there are no unstaged changes."""
        with patch("subprocess.run") as mock_run:
            # First call: check for unstaged changes
            diff_check = MagicMock()
            diff_check.returncode = 0  # No unstaged changes

            # Second call: check for staged changes
            staged_check = MagicMock()
            staged_check.returncode = 1  # There are already staged changes

            mock_run.side_effect = [diff_check, staged_check]

            result = git_commitai.check_staged_changes(auto_stage=True)

            assert result
            # git add -u should not be called since there are no unstaged changes

    def test_auto_stage_with_amend_conflicts(self):
        """Test that -a and --amend flags conflict."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.stdout", new=StringIO()) as fake_out:
                with pytest.raises(SystemExit) as exc_info:
                    with patch("sys.argv", ["git-commitai", "-a", "--amend"]):
                        git_commitai.main()

                output = fake_out.getvalue()
                assert exc_info.value.code == 1
                assert "Cannot use -a/--all with --amend" in output

    def test_create_commit_message_file_with_auto_staged(self):
        """Test that commit message file notes auto-staging."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = "M\tfile1.txt\nM\tfile2.txt"

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Test commit message", amend=False, auto_staged=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Test commit message" in content
                    assert "# Files were automatically staged using -a flag." in content

    def test_main_flow_with_auto_stage(self):
        """Test the main flow with -a flag."""
        with patch("subprocess.run") as mock_run:
            # Setup successful returns for all subprocess calls
            mock_run.return_value.returncode = 0

            # Mock the various checks and operations
            with patch("git_commitai.check_staged_changes", return_value=True) as mock_check:
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                        "repo_config": {}
                    }

                    with patch("git_commitai.make_api_request", return_value="Auto-staged commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-a"]):
                                                    git_commitai.main()

                                                    # Verify check_staged_changes was called with auto_stage=True
                                                    mock_check.assert_called_once_with(
                                                        amend=False,
                                                        auto_stage=True,
                                                        allow_empty=False
                                                    )

                                                    # Verify create_commit_message_file was called with auto_staged=True
                                                    mock_create.assert_called_once()
                                                    call_args = mock_create.call_args
                                                    assert call_args[1]["auto_staged"]

    def test_auto_stage_only_tracked_files(self):
        """Test that -a only stages tracked files, not untracked ones."""
        # This is more of a documentation test since git add -u inherently does this
        # But we verify the correct command is used
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            git_commitai.stage_all_tracked_files()

            # Verify it uses 'git add -u' which only stages tracked files
            # not 'git add -A' which would include untracked files
            mock_run.assert_called_with(
                ["git", "add", "-u"],  # -u is update, only tracked files
                check=True,
                capture_output=True,
            )
