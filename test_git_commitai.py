#!/usr/bin/env python3

import pytest
import os
import tempfile
import json
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Simple import now that it has .py extension
import git_commitai


class TestGitStatus:
    """Test the git status parsing and display functions."""

    def test_parse_porcelain_modified_files(self):
        """Test parsing modified files from git status --porcelain."""
        with patch("git_commitai.run_command") as mock_run:
            # Setup mock returns
            mock_run.side_effect = [
                "main",  # git branch --show-current
                "",  # git rev-parse HEAD (success, not initial commit)
                " M README.md\n M git-commitai\n?? LICENSE",  # git status --porcelain
            ]

            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                # Check that both modified files are shown
                assert "modified:   README.md" in output
                assert "modified:   git-commitai" in output
                assert "LICENSE" in output
                assert "Untracked files:" in output
                assert "Changes not staged for commit:" in output

    def test_parse_porcelain_staged_and_modified(self):
        """Test parsing files that are staged with additional modifications."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = [
                "main",
                "",
                "MM file1.txt\nM  file2.txt\n M file3.txt",
            ]

            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                # MM means staged with additional unstaged changes
                assert "modified:   file1.txt" in output
                # M  means staged only (not shown in unstaged)
                assert "modified:   file2.txt" not in output
                # _M means modified but not staged
                assert "modified:   file3.txt" in output

    def test_parse_porcelain_deleted_files(self):
        """Test parsing deleted files."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = ["main", "", " D deleted.txt\nD  staged_delete.txt"]

            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                assert "deleted:    deleted.txt" in output
                assert "deleted:    staged_delete.txt" not in output

    def test_clean_working_tree(self):
        """Test output when working tree is clean."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = [
                "main",
                "",
                "",  # No output from git status --porcelain
            ]

            with patch("sys.stdout", new=StringIO()) as fake_out:
                git_commitai.show_git_status()
                output = fake_out.getvalue()

                assert "nothing to commit, working tree clean" in output

    def test_initial_commit(self):
        """Test output for initial commit."""
        with patch("git_commitai.run_command") as mock_run:

            def side_effect(cmd, check=True):
                if "branch --show-current" in cmd:
                    return "main"
                elif "rev-parse HEAD" in cmd:
                    if check:
                        raise subprocess.CalledProcessError(1, cmd)
                    return ""
                elif "status --porcelain" in cmd:
                    return "?? README.md"
                return ""

            mock_run.side_effect = side_effect

            with patch("sys.stdout", new=StringIO()) as fake_out:
                # Mock CalledProcessError since it's used in the function
                with patch.object(subprocess, "CalledProcessError", Exception):
                    git_commitai.show_git_status()
                    output = fake_out.getvalue()

                    assert "Initial commit" in output
                    assert "Untracked files:" in output


class TestStagedFiles:
    """Test getting staged file contents."""

    def test_get_staged_files(self):
        """Test retrieving staged file contents."""
        with patch("git_commitai.run_command") as mock_run:
            # Mock the sequence of commands that will be called
            def side_effect(cmd, check=True):
                if "git diff --cached --name-only" in cmd:
                    return "file1.py\nfile2.md"
                elif "git diff --cached --numstat -- file1.py" in cmd:
                    return "10\t5\tfile1.py"  # Not binary (shows numbers)
                elif "git show :file1.py" in cmd:
                    return 'print("hello")'
                elif "git diff --cached --numstat -- file2.md" in cmd:
                    return "3\t1\tfile2.md"  # Not binary
                elif "git show :file2.md" in cmd:
                    return "# Header\nContent"
                return ""

            mock_run.side_effect = side_effect

            result = git_commitai.get_staged_files()

            assert "file1.py" in result
            assert 'print("hello")' in result
            assert "file2.md" in result
            assert "# Header" in result

    def test_get_staged_files_empty(self):
        """Test when no files are staged."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = ""

            result = git_commitai.get_staged_files()
            assert result == ""

    def test_get_staged_files_with_binary(self):
        """Test retrieving staged files including binary files."""
        with patch("git_commitai.run_command") as mock_run:

            def side_effect(cmd, check=True):
                if "git diff --cached --name-only" in cmd:
                    return "file1.py\nlogo.webp"
                elif "git diff --cached --numstat -- file1.py" in cmd:
                    return "10\t5\tfile1.py"  # Text file
                elif "git show :file1.py" in cmd:
                    return 'print("hello")'
                elif "git diff --cached --numstat -- logo.webp" in cmd:
                    return "-\t-\tlogo.webp"  # Binary file (shows dashes)
                elif "git cat-file -s :logo.webp" in cmd:
                    return "45678"  # File size in bytes
                return ""

            mock_run.side_effect = side_effect

            # Need to patch os.path.splitext for the binary file extension
            with patch("os.path.splitext", return_value=("logo", ".webp")):
                result = git_commitai.get_staged_files()

                assert "file1.py" in result
                assert 'print("hello")' in result
                assert "logo.webp (binary file)" in result
                assert "WebP image" in result or "File type: .webp" in result
                assert "KB" in result  # File size should be shown

    def test_get_staged_files_amend(self):
        """Test retrieving files for --amend."""
        with patch("git_commitai.run_command") as mock_run:

            def side_effect(cmd, check=True):
                if "git diff-tree --no-commit-id --name-only -r HEAD" in cmd:
                    return "file1.py\nfile2.md"
                elif "git diff --cached --name-only" in cmd:
                    return "file3.js"
                elif "git diff --cached --numstat -- file1.py" in cmd:
                    return "10\t5\tfile1.py"
                elif "git show :file1.py" in cmd:
                    return 'print("hello")'
                elif "git diff --cached --numstat -- file2.md" in cmd:
                    return "3\t1\tfile2.md"
                elif "git show :file2.md" in cmd:
                    return "# Header"
                elif "git diff --cached --numstat -- file3.js" in cmd:
                    return "1\t1\tfile3.js"
                elif "git show :file3.js" in cmd:
                    return 'console.log("test")'
                return ""

            mock_run.side_effect = side_effect

            result = git_commitai.get_staged_files(amend=True)

            assert "file1.py" in result
            assert "file2.md" in result
            assert "file3.js" in result

    def test_get_staged_files_binary_types(self):
        """Test different binary file types are properly identified."""
        test_cases = [
            ("image.png", "-\t-\timage.png", "PNG image"),
            ("video.mp4", "-\t-\tvideo.mp4", "MP4 video"),
            ("archive.zip", "-\t-\tarchive.zip", "ZIP archive"),
            ("font.ttf", "-\t-\tfont.ttf", "TrueType font"),
        ]

        for filename, numstat_output, expected_description in test_cases:
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-only" in cmd:
                        return filename
                    elif f"git diff --cached --numstat -- {filename}" in cmd:
                        return numstat_output
                    elif f"git cat-file -s :{filename}" in cmd:
                        return "1024"  # 1KB
                    return ""

                mock_run.side_effect = side_effect

                # Extract extension for os.path.splitext mock
                name, ext = filename.rsplit(".", 1)
                with patch("os.path.splitext", return_value=(name, f".{ext}")):
                    result = git_commitai.get_staged_files()

                    assert f"{filename} (binary file)" in result
                    assert (
                        expected_description in result or f"File type: .{ext}" in result
                    )


class TestCheckStagedChanges:
    """Test checking for staged changes."""

    def test_has_staged_changes(self):
        """Test when there are staged changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = (
                1  # git diff returns 1 when there are changes
            )

            assert git_commitai.check_staged_changes() == True

    def test_no_staged_changes(self):
        """Test when there are no staged changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0  # git diff returns 0 when no changes

            with patch("git_commitai.show_git_status"):
                assert git_commitai.check_staged_changes() == False

    def test_amend_with_previous_commit(self):
        """Test --amend with a previous commit."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = "abc123"  # Successful HEAD lookup

            assert git_commitai.check_staged_changes(amend=True) == True

    def test_amend_without_previous_commit(self):
        """Test --amend on initial commit."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "git rev-parse HEAD"
            )

            with patch("sys.stdout", new=StringIO()) as fake_out:
                result = git_commitai.check_staged_changes(amend=True)
                output = fake_out.getvalue()

                assert result == False
                assert "nothing to amend" in output


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


class TestAPIRequest:
    """Test API request handling."""

    def test_successful_api_request(self):
        """Test successful API request."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        mock_response = {
            "choices": [{"message": {"content": "Fix bug in authentication"}}]
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                json.dumps(mock_response).encode()
            )

            result = git_commitai.make_api_request(config, "test message")
            assert result == "Fix bug in authentication"

    def test_api_request_error(self):
        """Test API request error handling."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            from urllib.error import HTTPError

            mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", {}, None)

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")


class TestCommitMessageEmpty:
    """Test commit message empty checking with comprehensive comment line tests."""

    def test_empty_message(self):
        """Test detecting empty commit message."""
        content = """
# Please enter the commit message for your changes.
# Lines starting with '#' will be ignored.
#
# On branch main
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == True

    def test_non_empty_message(self):
        """Test detecting non-empty commit message."""
        content = """Fix authentication bug

This fixes the issue where users couldn't log in.

# Please enter the commit message for your changes.
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False

    def test_comments_with_leading_whitespace(self):
        """Test that comments with leading whitespace are properly ignored."""
        content = """
  # This is a comment with leading spaces
    # This is a comment with more spaces
	# This is a comment with a tab
# Regular comment

# All above lines should be ignored
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == True

    def test_mixed_content_and_comments(self):
        """Test message with both content and comments."""
        content = """Add new feature

  # This is a comment that should be ignored
This adds the new authentication feature.
    # Another comment with leading spaces

# Please enter the commit message for your changes.
# Lines starting with '#' will be ignored.
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False

    def test_only_whitespace_lines(self):
        """Test that lines with only whitespace are considered empty."""
        content = """



# Comment line
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == True

    def test_hash_in_content_not_comment(self):
        """Test that # in the middle of content is not treated as comment."""
        content = """Fix issue #123

This fixes bug #123 in the authentication system.

# This is an actual comment
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False

    def test_indented_content_preserved(self):
        """Test that indented content (not comments) is preserved."""
        content = """Refactor code structure

    - Move files to new directory
    - Update imports

# Comment line
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False

    def test_empty_file(self):
        """Test completely empty file."""
        content = ""
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == True

    def test_file_read_error(self):
        """Test handling of file read errors."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            assert git_commitai.is_commit_message_empty("fake_path") == True

    def test_single_non_comment_line(self):
        """Test file with just one non-comment line."""
        content = "Initial commit"
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False

    def test_comment_like_but_not_at_start(self):
        """Test that lines not starting with # (after stripping leading whitespace) are not comments."""
        content = """Update README.md # with new instructions

This updates the README file # adding more details

# This is a real comment
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path") == False


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


class TestCommitMessageFileCreation:
    """Test the creation of commit message files with proper comment formatting."""

    def test_create_commit_message_file_with_comments(self):
        """Test that commit message file is created with proper git-style comments."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = "M\tfile1.txt\nA\tfile2.txt"

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Test commit message", amend=False
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check that the message is there
                    assert "Test commit message" in content

                    # Check for git-style comments
                    assert "# Please enter the commit message" in content
                    assert "# with '#' will be ignored" in content
                    assert "# On branch main" in content
                    assert "# Changes to be committed:" in content

                    # Check that all comment lines start with #
                    for line in content.split("\n"):
                        if (
                            "Please enter" in line
                            or "will be ignored" in line
                            or "On branch" in line
                        ):
                            assert line.strip().startswith("#")

    def test_comments_properly_prefixed(self):
        """Test that all generated comments have # prefix."""
        with patch("git_commitai.get_current_branch", return_value="feature-branch"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = ""

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "My commit", amend=False
                    )

                    with open(commit_file, "r") as f:
                        lines = f.readlines()

                    # Find where comments start (after the commit message and blank line)
                    comment_start = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith("# Please enter"):
                            comment_start = i
                            break

                    assert comment_start is not None, "Comments section not found"

                    # All lines from comment_start should either be empty or start with #
                    for line in lines[comment_start:]:
                        line = line.strip()
                        if line:  # Non-empty lines
                            assert line.startswith(
                                "#"
                            ), f"Non-comment line found in comments section: {line}"


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

    def test_no_api_key(self):
        """Test behavior when API key is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                git_commitai.get_env_config()

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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Test commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch("sys.argv", ["git-commitai"]):
                                                git_commitai.main()

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

                    with patch(
                        "git_commitai.make_api_request", return_value="Amended commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "--amend"]
                                            ):
                                                git_commitai.main()

                                                # Verify git commit --amend was called
                                                calls = mock_run.call_args_list
                                                assert any(
                                                    [
                                                        "--amend" in str(call)
                                                        for call in calls
                                                    ]
                                                )


class TestAutoStageFlag:
    """Test the -a/--all auto-stage functionality."""

    def test_stage_all_tracked_files(self):
        """Test that stage_all_tracked_files calls git add -u."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = git_commitai.stage_all_tracked_files()

            assert result == True
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

            assert result == True
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

            assert result == True
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
            with patch("git_commitai.run_command") as mock_run:
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
            with patch(
                "git_commitai.check_staged_changes", return_value=True
            ) as mock_check:
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch(
                        "git_commitai.make_api_request",
                        return_value="Auto-staged commit",
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ) as mock_create:
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "-a"]
                                            ):
                                                git_commitai.main()

                                                # Verify check_staged_changes was called with auto_stage=True
                                                mock_check.assert_called_once_with(
                                                    amend=False, auto_stage=True
                                                )

                                                # Verify create_commit_message_file was called with auto_staged=True
                                                mock_create.assert_called_once()
                                                call_args = mock_create.call_args
                                                assert (
                                                    call_args[1]["auto_staged"] == True
                                                )

    def test_prompt_includes_auto_stage_note(self):
        """Test that the AI prompt mentions auto-staging when -a is used."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Test"
                    ) as mock_api:
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv",
                                                ["git-commitai", "-a", "-m", "context"],
                                            ):
                                                git_commitai.main()

                                                # Check that the prompt includes auto-stage note
                                                call_args = mock_api.call_args[0]
                                                prompt = call_args[1]
                                                assert (
                                                    "Files were automatically staged using the -a flag"
                                                    in prompt
                                                )
                                                assert "context" in prompt

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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Test commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "-n"]
                                            ):
                                                git_commitai.main()

                                                # Find the git commit call
                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                assert len(commit_calls) > 0

                                                # Verify --no-verify is in the command
                                                last_commit_call = commit_calls[-1]
                                                assert (
                                                    "--no-verify"
                                                    in last_commit_call[0][0]
                                                )

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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Test commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            # Test with -n shorthand
                                            with patch(
                                                "sys.argv", ["git-commitai", "-n"]
                                            ):
                                                git_commitai.main()

                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                last_commit_call = commit_calls[-1]
                                                assert (
                                                    "--no-verify"
                                                    in last_commit_call[0][0]
                                                )

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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Amended commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv",
                                                ["git-commitai", "--amend", "-n"],
                                            ):
                                                git_commitai.main()

                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                last_commit_call = commit_calls[-1]

                                                # Should have both --amend and --no-verify
                                                assert (
                                                    "--amend" in last_commit_call[0][0]
                                                )
                                                assert (
                                                    "--no-verify"
                                                    in last_commit_call[0][0]
                                                )

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
                    }

                    with patch(
                        "git_commitai.make_api_request",
                        return_value="Auto-staged commit",
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "-a", "-n"]
                                            ):
                                                git_commitai.main()

                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                last_commit_call = commit_calls[-1]
                                                assert (
                                                    "--no-verify"
                                                    in last_commit_call[0][0]
                                                )

    def test_create_commit_message_file_with_no_verify(self):
        """Test that commit message file notes when hooks will be skipped."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Test"
                    ) as mock_api:
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "-n"]
                                            ):
                                                git_commitai.main()

                                                # Check that the prompt includes no-verify note
                                                call_args = mock_api.call_args[0]
                                                prompt = call_args[1]
                                                assert (
                                                    "Git hooks will be skipped"
                                                    in prompt
                                                )
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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Complex commit"
                    ) as mock_api:
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ) as mock_create:
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            # Combine -a, -n, and -m flags
                                            with patch(
                                                "sys.argv",
                                                [
                                                    "git-commitai",
                                                    "-a",
                                                    "-n",
                                                    "-m",
                                                    "quick fix",
                                                ],
                                            ):
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
                                                assert (
                                                    create_args["auto_staged"] == True
                                                )
                                                assert create_args["no_verify"] == True

                                                # Check git commit command
                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                if commit_calls:
                                                    last_commit_call = commit_calls[-1]
                                                    assert (
                                                        "--no-verify"
                                                        in last_commit_call[0][0]
                                                    )

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
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Normal commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ):
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch("sys.argv", ["git-commitai"]):
                                                git_commitai.main()

                                                # Verify --no-verify is NOT in the command
                                                commit_calls = [
                                                    call
                                                    for call in mock_run.call_args_list
                                                    if "commit" in str(call)
                                                ]
                                                if commit_calls:
                                                    last_commit_call = commit_calls[-1]
                                                    assert (
                                                        "--no-verify"
                                                        not in last_commit_call[0][0]
                                                    )


class TestVerboseFlag:
    """Test the -v/--verbose diff display functionality."""

    def test_create_commit_message_file_with_verbose(self):
        """Test that verbose flag adds diff to commit message file."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "M\tfile1.txt\nA\tfile2.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/file1.txt b/file1.txt
index 123..456 100644
--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,3 @@
-old line
+new line
 unchanged line"""
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Test commit message",
                        amend=False,
                        auto_staged=False,
                        no_verify=False,
                        verbose=True,
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check for commit message
                    assert "Test commit message" in content

                    # Check for verbose separator
                    assert (
                        "# ------------------------ >8 ------------------------"
                        in content
                    )
                    assert "# Do not modify or remove the line above." in content
                    assert "# Everything below it will be ignored." in content

                    # Check for diff header
                    assert "# Diff of changes to be committed:" in content

                    # Check for actual diff content (as comments)
                    assert "# diff --git a/file1.txt b/file1.txt" in content
                    assert "# -old line" in content
                    assert "# +new line" in content

    def test_verbose_without_diff(self):
        """Test verbose mode when there's no diff to show."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = ""  # No diff

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Empty commit", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Verbose section should still be present
                    assert (
                        "# ------------------------ >8 ------------------------"
                        in content
                    )
                    assert "# Diff of changes to be committed:" in content

    def test_verbose_with_amend(self):
        """Test verbose flag with --amend shows correct diff."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git rev-parse HEAD^" in cmd:
                        return "abc123"
                    elif "git diff abc123..HEAD" in cmd:
                        return """diff --git a/original.txt b/original.txt
index 111..222 100644
--- a/original.txt
+++ b/original.txt
@@ -1 +1 @@
-original content
+amended content"""
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/new.txt b/new.txt
new file mode 100644
index 000..333
--- /dev/null
+++ b/new.txt
@@ -0,0 +1 @@
+new file content"""
                    elif "git diff-tree" in cmd:
                        return "M\toriginal.txt"
                    elif "git diff --cached --name-status" in cmd:
                        return "A\tnew.txt"
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Amended commit", amend=True, verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Should show both original commit diff and new staged changes
                    assert "# diff --git a/original.txt b/original.txt" in content
                    assert "# -original content" in content
                    assert "# +amended content" in content

                    # Should also show additional staged changes
                    assert "# Additional staged changes:" in content
                    assert "# diff --git a/new.txt b/new.txt" in content
                    assert "# +new file content" in content

    def test_verbose_with_binary_files(self):
        """Test verbose mode properly handles binary files in diff."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "A\tlogo.png\nM\tcode.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return """diff --git a/logo.png b/logo.png
new file mode 100644
index 000..111
Binary files /dev/null and b/logo.png differ
diff --git a/code.py b/code.py
index 222..333 100644
--- a/code.py
+++ b/code.py
@@ -1 +1 @@
-print("old")
+print("new")"""
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Added logo and updated code", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check for binary file indication
                    assert "# Binary files /dev/null and b/logo.png differ" in content

                    # Check for text file diff
                    assert '# -print("old")' in content
                    assert '# +print("new")' in content

    def test_main_flow_with_verbose(self):
        """Test the main flow with -v flag."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Verbose commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ) as mock_create:
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            with patch(
                                                "sys.argv", ["git-commitai", "-v"]
                                            ):
                                                git_commitai.main()

                                                # Verify create_commit_message_file was called with verbose=True
                                                mock_create.assert_called_once()
                                                call_args = mock_create.call_args[1]
                                                assert call_args["verbose"] == True

    def test_verbose_with_multiple_flags(self):
        """Test verbose combined with other flags."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test",
                        "api_url": "http://test",
                        "model": "test",
                    }

                    with patch(
                        "git_commitai.make_api_request", return_value="Complex commit"
                    ):
                        with patch(
                            "git_commitai.get_git_dir", return_value="/tmp/.git"
                        ):
                            with patch(
                                "git_commitai.create_commit_message_file",
                                return_value="/tmp/COMMIT",
                            ) as mock_create:
                                with patch(
                                    "os.path.getmtime", side_effect=[1000, 2000]
                                ):
                                    with patch("git_commitai.open_editor"):
                                        with patch(
                                            "git_commitai.is_commit_message_empty",
                                            return_value=False,
                                        ):
                                            # Combine -a, -n, -v flags
                                            with patch(
                                                "sys.argv",
                                                ["git-commitai", "-a", "-n", "-v"],
                                            ):
                                                git_commitai.main()

                                                # Verify all flags are passed correctly
                                                call_args = mock_create.call_args[1]
                                                assert call_args["auto_staged"] == True
                                                assert call_args["no_verify"] == True
                                                assert call_args["verbose"] == True

    def test_verbose_diff_formatting(self):
        """Test that diff lines are properly formatted as comments."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                # Multi-line diff with various git diff elements
                complex_diff = """diff --git a/src/main.py b/src/main.py
index abc123..def456 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,7 @@ def main():
     # Initialize application
     app = Application()

-    # Old configuration
+    # New configuration
     config = load_config()

@@ -20,3 +20,5 @@ def main():
     app.run()
+
+    return 0"""

                def side_effect(cmd, check=True):
                    if "git diff --cached --name-status" in cmd:
                        return "M\tsrc/main.py"
                    elif "git diff --cached" in cmd and "--name-status" not in cmd:
                        return complex_diff
                    return ""

                mock_run.side_effect = side_effect

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Update configuration", verbose=True
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Every diff line should be commented
                    for line in complex_diff.split("\n"):
                        assert f"# {line}" in content

                    # Check specific formatting
                    assert "# @@ -10,7 +10,7 @@ def main():" in content
                    assert "# -    # Old configuration" in content
                    assert "# +    # New configuration" in content
                    assert "# +    return 0" in content

    def test_verbose_separator_not_in_normal_mode(self):
        """Test that verbose separator is not added without -v flag."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_command") as mock_run:
                mock_run.return_value = "M\tfile.txt"

                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir, "Normal commit", verbose=False  # Not verbose
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Verbose separator should NOT be present
                    assert (
                        "# ------------------------ >8 ------------------------"
                        not in content
                    )
                    assert "# Diff of changes to be committed:" not in content


# Add this if running as a script
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=git_commitai", "--cov-report=term-missing"])
