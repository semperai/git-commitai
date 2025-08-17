"""Tests for utility functions."""

import pytest
import subprocess
import os
from unittest.mock import patch
import git_commitai


class TestGitEditor:
    """Test git editor detection."""

    def test_git_editor_env(self):
        """Test GIT_EDITOR environment variable."""
        with patch.dict(os.environ, {"GIT_EDITOR": "nano"}):
            assert git_commitai.get_git_editor() == "nano"

    def test_editor_env(self):
        """Test EDITOR environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {"EDITOR": "vim"}):
                assert git_commitai.get_git_editor() == "vim"

    def test_git_config_editor(self):
        """Test git config core.editor."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = "emacs"
                assert git_commitai.get_git_editor() == "emacs"

    def test_default_editor(self):
        """Test default editor fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = ""
                assert git_commitai.get_git_editor() == "vi"


class TestGitUtilities:
    """Test git-related utility functions."""

    def test_get_current_branch(self):
        """Test getting current branch name."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "main"
            assert git_commitai.get_current_branch() == "main"

    def test_get_current_branch_detached(self):
        """Test getting branch name in detached HEAD state."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.side_effect = ["", "abc123"]  # Empty branch name, then short SHA
            assert git_commitai.get_current_branch() == "abc123"

    def test_get_git_dir(self):
        """Test getting git directory path."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "/path/to/.git"
            assert git_commitai.get_git_dir() == "/path/to/.git"

    def test_run_git_success(self):
        """Test successful git command execution."""
        with patch("subprocess.run") as mock_run:
            mock_result = subprocess.CompletedProcess(
                args=["git", "status"],
                returncode=0,
                stdout="On branch main",
                stderr=""
            )
            mock_run.return_value = mock_result

            result = git_commitai.run_git(["status"])
            assert result == "On branch main"
            mock_run.assert_called_once_with(
                ["git", "status"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_run_git_failure(self):
        """Test git command execution failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["git", "invalid-command"], stderr="git: 'invalid-command' is not a git command"
            )

            with pytest.raises(subprocess.CalledProcessError):
                git_commitai.run_git(["invalid-command"], check=True)

    def test_run_git_no_check(self):
        """Test git command with check=False."""
        with patch("subprocess.run") as mock_run:
            # When check=False, CalledProcessError is not raised
            mock_result = subprocess.CompletedProcess(
                args=["git", "status"],
                returncode=1,
                stdout="error output",
                stderr=""
            )
            mock_run.return_value = mock_result

            result = git_commitai.run_git(["status"], check=False)
            assert result == "error output"


class TestBinaryFileInfo:
    """Test binary file information extraction."""

    def test_get_binary_file_info_with_extension(self):
        """Test getting info for binary file with known extension."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "1024"  # File size

            with patch("os.path.splitext", return_value=("image", ".png")):
                info = git_commitai.get_binary_file_info("image.png")

                assert "File type: .png" in info
                assert "1.0 KB" in info
                assert "PNG image" in info

    def test_get_binary_file_info_unknown_extension(self):
        """Test getting info for binary file with unknown extension."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = ""  # No size info

            with patch("os.path.splitext", return_value=("file", ".xyz")):
                info = git_commitai.get_binary_file_info("file.xyz")

                assert "File type: .xyz" in info or "no additional information" in info

    def test_get_binary_file_info_new_vs_modified(self):
        """Test detecting new vs modified binary files."""
        with patch("git_commitai.run_git") as mock_run:
            # Test new file
            def side_effect_new(args, check=True):
                if "cat-file" in args and "-s" in args:
                    return "1024"
                elif "cat-file" in args and "-e" in args and "HEAD:" in str(args):
                    if check:
                        raise subprocess.CalledProcessError(1, args)
                return ""

            mock_run.side_effect = side_effect_new
            with patch("os.path.splitext", return_value=("new", ".bin")):
                info = git_commitai.get_binary_file_info("new.bin")
                assert "New file" in info

            # Test modified file
            mock_run.side_effect = ["1024", ""]  # Size, then successful HEAD check
            with patch("os.path.splitext", return_value=("modified", ".bin")):
                info = git_commitai.get_binary_file_info("modified.bin")
                assert "Modified" in info


class TestOpenEditor:
    """Test editor opening functionality."""

    def test_open_editor_success(self):
        """Test successfully opening editor."""
        with patch("subprocess.run") as mock_run:
            git_commitai.open_editor("/tmp/file", "vim")
            mock_run.assert_called_once_with(["vim", "/tmp/file"])

    def test_open_editor_with_complex_editor(self):
        """Test opening editor with complex command (e.g., 'code --wait')."""
        with patch("subprocess.run") as mock_run:
            with patch("git_commitai.shlex.split", return_value=["code", "--wait"]):
                git_commitai.open_editor("/tmp/file", "code --wait")
                mock_run.assert_called_once_with(["code", "--wait", "/tmp/file"])

    def test_open_editor_failure(self):
        """Test handling editor open failure."""
        with patch("subprocess.run", side_effect=Exception("Editor failed")):
            with pytest.raises(SystemExit):
                git_commitai.open_editor("/tmp/file", "nonexistent-editor")
