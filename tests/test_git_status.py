"""Tests for git status parsing and display functions."""

import subprocess
from unittest.mock import patch
from io import StringIO

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
                git_commitai.show_git_status()


class TestCheckStagedChanges:
    """Test checking for staged changes."""

    def test_has_staged_changes(self):
        """Test when there are staged changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1  # git diff returns 1 when there are changes

            assert git_commitai.check_staged_changes()

    def test_no_staged_changes(self):
        """Test when there are no staged changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0  # git diff returns 0 when no changes

            with patch("git_commitai.show_git_status"):
                assert not git_commitai.check_staged_changes()

    def test_amend_with_previous_commit(self):
        """Test --amend with a previous commit."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.return_value = "abc123"  # Successful HEAD lookup

            assert git_commitai.check_staged_changes(amend=True)

    def test_amend_without_previous_commit(self):
        """Test --amend on initial commit."""
        with patch("git_commitai.run_command") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse HEAD")

            with patch("sys.stdout", new=StringIO()) as fake_out:
                result = git_commitai.check_staged_changes(amend=True)
                output = fake_out.getvalue()

                assert not result
                assert "nothing to amend" in output
