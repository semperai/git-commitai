"""Tests for --dry-run functionality."""

import sys
import argparse
from io import StringIO
from unittest.mock import patch, MagicMock, Mock

import git_commitai


class TestDryRunFlag:
    """Test the --dry-run functionality."""

    def test_show_dry_run_summary_basic(self):
        """Test basic dry run summary output."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = "M\tsrc/main.py\nA\ttests/test_main.py"

                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    # Create mock args using argparse.Namespace
                    args = argparse.Namespace(
                        amend=False,
                        allow_empty=False,
                        no_verify=False,
                        author=None,
                        date=None,
                        all=False,
                        message=None,
                        verbose=False,
                        dry_run=True,
                        debug=False,
                        api_key=None,
                        api_url=None,
                        model=None
                    )

                    git_commitai.show_dry_run_summary(
                        "Add unit tests for main module\n\nAdded comprehensive test coverage",
                        args
                    )

                output = captured_output.getvalue()

                # Check header
                assert "# Dry run mode - no commit will be created" in output
                assert "# On branch main" in output

                # Check changes to be committed
                assert "# Changes to be committed:" in output
                assert "#   M\tsrc/main.py" in output
                assert "#   A\ttests/test_main.py" in output

                # Check generated commit message
                assert "# Generated commit message:" in output
                assert "# Add unit tests for main module" in output
                assert "# Added comprehensive test coverage" in output

                # Check footer
                assert "# To actually commit these changes, run without --dry-run" in output

    def test_show_dry_run_summary_with_amend(self):
        """Test dry run summary with --amend flag."""
        with patch("git_commitai.get_current_branch", return_value="develop"):
            # Capture stdout
            captured_output = StringIO()
            with patch("sys.stdout", captured_output):
                # Create mock args using argparse.Namespace
                args = argparse.Namespace(
                    amend=True,
                    allow_empty=False,
                    no_verify=False,
                    author=None,
                    date=None,
                    all=False,
                    message=None,
                    verbose=False,
                    dry_run=True,
                    debug=False,
                    api_key=None,
                    api_url=None,
                    model=None
                )

                git_commitai.show_dry_run_summary(
                    "Fix: Correct previous commit",
                    args
                )

            output = captured_output.getvalue()

            # Should show amend message
            assert "# Would amend the previous commit" in output
            assert "# On branch develop" in output

    def test_show_dry_run_summary_with_allow_empty(self):
        """Test dry run summary with --allow-empty flag."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            # Capture stdout
            captured_output = StringIO()
            with patch("sys.stdout", captured_output):
                # Create mock args using argparse.Namespace
                args = argparse.Namespace(
                    amend=False,
                    allow_empty=True,
                    no_verify=False,
                    author=None,
                    date=None,
                    all=False,
                    message=None,
                    verbose=False,
                    dry_run=True,
                    debug=False,
                    api_key=None,
                    api_url=None,
                    model=None
                )

                git_commitai.show_dry_run_summary(
                    "Trigger CI pipeline",
                    args
                )

            output = captured_output.getvalue()

            # Should show empty commit message
            assert "# Would create an empty commit" in output

    def test_show_dry_run_summary_with_options(self):
        """Test dry run summary with various options."""
        with patch("git_commitai.get_current_branch", return_value="feature/test"):
            with patch("git_commitai.run_git", return_value="M\tREADME.md"):
                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    # Create mock args with various options
                    args = argparse.Namespace(
                        amend=False,
                        allow_empty=False,
                        no_verify=True,
                        author="John Doe <john@example.com>",
                        date="2024-01-01 12:00:00",
                        all=False,
                        message=None,
                        verbose=False,
                        dry_run=True,
                        debug=False,
                        api_key=None,
                        api_url=None,
                        model=None
                    )

                    git_commitai.show_dry_run_summary(
                        "Update documentation",
                        args
                    )

                output = captured_output.getvalue()

                # Check options are displayed
                assert "# (git hooks would be skipped)" in output
                assert "# (author would be: John Doe <john@example.com>)" in output
                assert "# (date would be: 2024-01-01 12:00:00)" in output

    def test_show_dry_run_summary_multiline_message(self):
        """Test dry run summary with multi-line commit message."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git", return_value="M\tapp.py"):
                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    args = argparse.Namespace(
                        amend=False,
                        allow_empty=False,
                        no_verify=False,
                        author=None,
                        date=None,
                        all=False,
                        message=None,
                        verbose=False,
                        dry_run=True,
                        debug=False,
                        api_key=None,
                        api_url=None,
                        model=None
                    )

                    # Multi-line commit message
                    commit_message = """Refactor authentication module

- Extract JWT validation to separate function
- Add refresh token support
- Improve error handling
- Update tests"""

                    git_commitai.show_dry_run_summary(commit_message, args)

                output = captured_output.getvalue()

                # Check all lines are properly formatted
                assert "# Refactor authentication module" in output
                assert "# - Extract JWT validation to separate function" in output
                assert "# - Add refresh token support" in output
                assert "# - Improve error handling" in output
                assert "# - Update tests" in output

    def test_show_dry_run_summary_with_warnings(self):
        """Test dry run summary with AI-generated warnings."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git", return_value="M\tconfig.py"):
                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    args = argparse.Namespace(
                        amend=False,
                        allow_empty=False,
                        no_verify=False,
                        author=None,
                        date=None,
                        all=False,
                        message=None,
                        verbose=False,
                        dry_run=True,
                        debug=False,
                        api_key=None,
                        api_url=None,
                        model=None
                    )

                    # Commit message with warnings
                    commit_message = """Update configuration

# ⚠️  WARNING: Hardcoded API key detected
# Found in: config.py
# Details: API key should be in environment variables"""

                    git_commitai.show_dry_run_summary(commit_message, args)

                output = captured_output.getvalue()

                # Check message and warnings are displayed
                assert "# Update configuration" in output
                assert "# # ⚠️  WARNING: Hardcoded API key detected" in output
                assert "# # Found in: config.py" in output

    def test_main_flow_with_dry_run(self):
        """Test the main flow with --dry-run flag."""
        test_argv = ["git-commitai", "--dry-run"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Test commit"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        # Catch the sys.exit(0) that happens after dry-run
                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            try:
                                                git_commitai.main()
                                            except SystemExit:
                                                pass  # Expected

                                            # Verify dry run summary was shown
                                            mock_show_summary.assert_called_once()
                                            call_args = mock_show_summary.call_args[0]
                                            assert call_args[0] == "Test commit"  # commit message

                                            # Verify we exited with 0
                                            mock_exit.assert_called_with(0)

    def test_dry_run_with_no_changes(self):
        """Test dry run when there are no staged changes."""
        test_argv = ["git-commitai", "--dry-run"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=False):
                    with patch("git_commitai.show_git_status"):  # Mock status output
                        # Catch the sys.exit(1) that happens when no changes
                        with patch("sys.exit") as mock_exit:
                            mock_exit.side_effect = SystemExit(1)

                            try:
                                git_commitai.main()
                            except SystemExit:
                                pass  # Expected

                            # Should exit with 1 when no changes
                            mock_exit.assert_called_with(1)

    def test_dry_run_with_auto_stage(self):
        """Test dry run with -a flag for auto-staging."""
        test_argv = ["git-commitai", "--dry-run", "-a"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Auto-staged commit"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        # Catch the sys.exit(0) that happens after dry-run
                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            try:
                                                git_commitai.main()
                                            except SystemExit:
                                                pass  # Expected

                                            # Verify auto-stage was passed through
                                            mock_show_summary.assert_called_once()
                                            args = mock_show_summary.call_args[0][1]
                                            assert args.all is True

    def test_dry_run_combined_with_verbose(self):
        """Test that --dry-run and -v can be used together."""
        test_argv = ["git-commitai", "--dry-run", "-v"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Verbose dry run"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        # Catch the sys.exit(0) that happens after dry-run
                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            try:
                                                git_commitai.main()
                                            except SystemExit:
                                                pass  # Expected

                                            # Dry run should work (verbose is ignored in dry-run)
                                            mock_show_summary.assert_called_once()
                                            mock_exit.assert_called_with(0)

    def test_dry_run_with_amend(self):
        """Test dry run with --amend flag."""
        test_argv = ["git-commitai", "--dry-run", "--amend"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Amended commit"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        # Catch the sys.exit(0) that happens after dry-run
                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            try:
                                                git_commitai.main()
                                            except SystemExit:
                                                pass  # Expected

                                            # Verify amend was passed through
                                            args = mock_show_summary.call_args[0][1]
                                            assert args.amend is True

    def test_dry_run_with_context_message(self):
        """Test dry run with -m context message."""
        test_argv = ["git-commitai", "--dry-run", "-m", "Fixed bug"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.build_ai_prompt") as mock_build_prompt:
                            mock_build_prompt.return_value = "prompt with context"

                            with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.make_api_request", return_value="Context-aware commit"):
                                        with patch("git_commitai.show_dry_run_summary"):
                                            # Catch the sys.exit(0) that happens after dry-run
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                try:
                                                    git_commitai.main()
                                                except SystemExit:
                                                    pass  # Expected

                                                # Verify context was passed to prompt builder
                                                mock_build_prompt.assert_called_once()
                                                args = mock_build_prompt.call_args[0][1]
                                                assert args.message == "Fixed bug"

    def test_dry_run_output_format(self):
        """Test the exact format of dry run output."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git") as mock_run:
                mock_run.return_value = "M\tfile1.py\nA\tfile2.py\nD\tfile3.py"

                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    args = argparse.Namespace(
                        amend=False,
                        allow_empty=False,
                        no_verify=False,
                        author=None,
                        date=None,
                        all=False,
                        message=None,
                        verbose=False,
                        dry_run=True,
                        debug=False,
                        api_key=None,
                        api_url=None,
                        model=None
                    )

                    git_commitai.show_dry_run_summary("Simple commit", args)

                output = captured_output.getvalue()
                lines = output.split('\n')

                # Check exact format
                assert lines[0] == "# Dry run mode - no commit will be created"
                assert lines[1] == "#"
                assert lines[2] == "# On branch main"
                assert "# Changes to be committed:" in output
                assert "#   M\tfile1.py" in output
                assert "#   A\tfile2.py" in output
                assert "#   D\tfile3.py" in output

    def test_dry_run_does_not_create_commit_file(self):
        """Test that dry run doesn't create COMMIT_EDITMSG file."""
        test_argv = ["git-commitai", "--dry-run"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Test"):
                                    with patch("git_commitai.show_dry_run_summary"):
                                        with patch("git_commitai.create_commit_message_file") as mock_create:
                                            # Catch the sys.exit(0) that happens after dry-run
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                try:
                                                    git_commitai.main()
                                                except SystemExit:
                                                    pass  # Expected

                                                # create_commit_message_file should NOT be called
                                                mock_create.assert_not_called()

    def test_dry_run_does_not_open_editor(self):
        """Test that dry run doesn't open the editor."""
        test_argv = ["git-commitai", "--dry-run"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Test"):
                                    with patch("git_commitai.show_dry_run_summary"):
                                        with patch("git_commitai.open_editor") as mock_editor:
                                            # Catch the sys.exit(0) that happens after dry-run
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                try:
                                                    git_commitai.main()
                                                except SystemExit:
                                                    pass  # Expected

                                                # Editor should NOT be opened
                                                mock_editor.assert_not_called()

    def test_dry_run_with_debug(self):
        """Test dry run with debug mode enabled."""
        test_argv = ["git-commitai", "--dry-run", "--debug"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    with patch("git_commitai.get_env_config") as mock_config:
                        mock_config.return_value = {
                            "api_key": "test",
                            "api_url": "http://test",
                            "model": "test",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="```\ndiff\n```"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.make_api_request", return_value="Debug test"):
                                    with patch("git_commitai.show_dry_run_summary"):
                                        with patch("git_commitai.debug_log") as mock_debug:
                                            # Catch the sys.exit(0) that happens after dry-run
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                try:
                                                    git_commitai.main()
                                                except SystemExit:
                                                    pass  # Expected

                                                # Debug log should mention dry-run mode
                                                debug_calls = [str(call) for call in mock_debug.call_args_list]
                                                assert any("DRY RUN MODE" in str(call) or "dry-run" in str(call).lower()
                                                          for call in debug_calls)
