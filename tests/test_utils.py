"""Tests for utility functions."""

import pytest
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
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = "emacs"
                assert git_commitai.get_git_editor() == "emacs"

    def test_default_editor(self):
        """Test default editor fallback."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = ""
                assert git_commitai.get_git_editor() == "vi"


class TestGitUtilities:
    """Test git-related utility functions."""

    def test_get_current_branch(self):
        """Test getting current branch name."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = "main"
            assert git_commitai.get_current_branch() == "main"

    def test_get_current_branch_detached(self):
        """Test getting branch name in detached HEAD state."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = ["", "abc123"]  # Empty branch name, then short SHA
            assert git_commitai.get_current_branch() == "abc123"

    def test_get_git_dir(self):
        """Test getting git directory path."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = "/path/to/.git"
            assert git_commitai.get_git_dir() == "/path/to/.git"

    def test_run_command_success(self):
        """Test successful command execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "output"
            mock_run.return_value.returncode = 0
            result = git_commitai.run_command("echo test")
            assert result == "output"

    def test_run_command_failure(self):
        """Test command execution failure."""
        with patch("subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

            with pytest.raises(subprocess.CalledProcessError):
                git_commitai.run_command("failing command", check=True)


class TestBinaryFileInfo:
    """Test binary file information extraction."""

    def test_get_binary_file_info_with_extension(self):
        """Test getting info for binary file with known extension."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = "1024"  # File size

            with patch("os.path.splitext", return_value=("image", ".png")):
                info = git_commitai.get_binary_file_info("image.png")

                assert "File type: .png" in info
                assert "1.0 KB" in info
                assert "PNG image" in info

    def test_get_binary_file_info_unknown_extension(self):
        """Test getting info for binary file with unknown extension."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = ""  # No size info

            with patch("os.path.splitext", return_value=("file", ".xyz")):
                info = git_commitai.get_binary_file_info("file.xyz")

                assert "File type: .xyz" in info or "no additional information" in info

    def test_get_binary_file_info_new_vs_modified(self):
        """Test detecting new vs modified binary files."""
        with patch("git_commitai.run_command") as mock_run:
            # Test new file
            def side_effect_new(cmd, check=True):
                if "cat-file -s" in cmd:
                    return "1024"
                elif "cat-file -e HEAD:" in cmd:
                    if check:
                        raise subprocess.CalledProcessError(1, cmd)
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

    def test_open_editor_failure(self):
        """Test handling editor open failure."""
        with patch("subprocess.run", side_effect=Exception("Editor failed")):
            with pytest.raises(SystemExit):
                git_commitai.open_editor("/tmp/file", "nonexistent-editor")
