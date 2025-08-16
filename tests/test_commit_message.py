"""Tests for commit message creation and validation."""

import pytest
import tempfile
from unittest.mock import patch, mock_open
import git_commitai


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
            assert git_commitai.is_commit_message_empty("fake_path")

    def test_non_empty_message(self):
        """Test detecting non-empty commit message."""
        content = """Fix authentication bug

This fixes the issue where users couldn't log in.

# Please enter the commit message for your changes.
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert not git_commitai.is_commit_message_empty("fake_path")

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
            assert git_commitai.is_commit_message_empty("fake_path")

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
            assert not git_commitai.is_commit_message_empty("fake_path")

    def test_only_whitespace_lines(self):
        """Test that lines with only whitespace are considered empty."""
        content = """



# Comment line
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path")

    def test_hash_in_content_not_comment(self):
        """Test that # in the middle of content is not treated as comment."""
        content = """Fix issue #123

This fixes bug #123 in the authentication system.

# This is an actual comment
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert not git_commitai.is_commit_message_empty("fake_path")

    def test_indented_content_preserved(self):
        """Test that indented content (not comments) is preserved."""
        content = """Refactor code structure

    - Move files to new directory
    - Update imports

# Comment line
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert not git_commitai.is_commit_message_empty("fake_path")

    def test_empty_file(self):
        """Test completely empty file."""
        content = ""
        with patch("builtins.open", mock_open(read_data=content)):
            assert git_commitai.is_commit_message_empty("fake_path")

    def test_file_read_error(self):
        """Test handling of file read errors."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            assert git_commitai.is_commit_message_empty("fake_path")

    def test_single_non_comment_line(self):
        """Test file with just one non-comment line."""
        content = "Initial commit"
        with patch("builtins.open", mock_open(read_data=content)):
            assert not git_commitai.is_commit_message_empty("fake_path")

    def test_comment_like_but_not_at_start(self):
        """Test that lines not starting with # (after stripping leading whitespace) are not comments."""
        content = """Update README.md # with new instructions

This updates the README file # adding more details

# This is a real comment
        """
        with patch("builtins.open", mock_open(read_data=content)):
            assert not git_commitai.is_commit_message_empty("fake_path")


class TestCommitMessageFileCreation:
    """Test the creation of commit message files with proper comment formatting."""

    def test_create_commit_message_file_with_comments(self):
        """Test that commit message file is created with proper git-style comments."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
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
            with patch("git_commitai.run_git") as mock_run:
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
                            assert line.startswith("#"), f"Non-comment line found in comments section: {line}"
