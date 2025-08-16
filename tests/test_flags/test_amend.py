"""Tests for --amend flag functionality."""

import tempfile
import subprocess
from unittest.mock import patch
import git_commitai


class TestAmendFeatures:
    """Test --amend specific features."""

    def test_get_git_diff_amend(self):
        """Test getting diff for --amend."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = [
                "abc123",  # git rev-parse HEAD^
                "diff --git a/file.txt...",  # git diff parent..HEAD
                "",  # git diff --cached (no additional staged changes)
            ]

            result = git_commitai.get_git_diff(amend=True)
            assert "diff --git a/file.txt" in result

    def test_get_git_diff_amend_with_staged(self):
        """Test getting diff for --amend with additional staged changes."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = [
                "abc123",  # git rev-parse HEAD^
                "diff --git a/file1.txt...",  # git diff parent..HEAD
                "diff --git a/file2.txt...",  # git diff --cached (additional staged)
            ]

            result = git_commitai.get_git_diff(amend=True)
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert "Additional staged changes" in result

    def test_create_commit_message_file_amend(self):
        """Test creating commit message file for --amend."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.side_effect = [
                    "M\tfile1.txt\nA\tfile2.txt",  # git diff-tree
                    "M\tfile3.txt",  # git diff --cached
                ]

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Test commit message", amend=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Test commit message" in content
                    assert "You are amending the previous commit" in content
                    assert "including previous commit" in content
                    assert "Additional staged changes" in content

    def test_successful_amend(self):
        """Test successful --amend flow."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch("git_commitai.make_api_request", return_value="Amended commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("sys.argv", ["git-commitai", "--amend"]):
                                                git_commitai.main()

                                                # Verify git commit --amend was called
                                                calls = mock_run.call_args_list
                                                assert any(["--amend" in str(call) for call in calls])

    def test_amend_first_commit(self):
        """Test --amend on the first commit (no parent)."""
        with patch("git_commitai.run_command") as mock_run:
            def side_effect(cmd, check=True):
                if "git rev-parse HEAD^" in cmd:
                    raise subprocess.CalledProcessError(1, cmd)
                elif "git diff --cached" in cmd:
                    return "diff --git a/file.txt..."
                return ""

            mock_run.side_effect = side_effect

            result = git_commitai.get_git_diff(amend=True)
            assert "diff --git a/file.txt" in result
