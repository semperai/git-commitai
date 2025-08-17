"""Tests for --dry-run functionality."""

import argparse
from unittest.mock import patch
from contextlib import suppress

import git_commitai


class TestDryRunFlag:
    """Test the --dry-run functionality."""

    def test_show_dry_run_summary_basic(self):
        """Test basic dry run delegates to git commit --dry-run."""
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

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(0)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Verify git commit --dry-run was called
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert call_args[:3] == ["git", "commit", "--dry-run"]

                # Should exit with git's return code
                mock_exit.assert_called_with(0)

    def test_show_dry_run_summary_with_amend(self):
        """Test dry run with --amend flag passes it to git."""
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

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(0)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Verify --amend was passed to git
                call_args = mock_run.call_args[0][0]
                assert "--amend" in call_args

    def test_show_dry_run_summary_with_allow_empty(self):
        """Test dry run with --allow-empty flag passes it to git."""
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

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(0)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Verify --allow-empty was passed to git
                call_args = mock_run.call_args[0][0]
                assert "--allow-empty" in call_args

    def test_show_dry_run_summary_with_options(self):
        """Test dry run with various options passes them to git."""
        args = argparse.Namespace(
            amend=False,
            allow_empty=False,
            no_verify=True,
            author="John Doe <john@example.com>",
            date="2024-01-01 12:00:00",
            all=False,
            message="Test message",
            verbose=True,
            dry_run=True,
            debug=False,
            api_key=None,
            api_url=None,
            model=None
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(0)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Verify all options were passed to git
                call_args = mock_run.call_args[0][0]
                assert "--no-verify" in call_args
                assert "--verbose" in call_args
                assert "--author" in call_args
                assert "John Doe <john@example.com>" in call_args
                assert "--date" in call_args
                assert "2024-01-01 12:00:00" in call_args
                # Message is added as placeholder
                assert "-m" in call_args

    def test_show_dry_run_summary_git_failure(self):
        """Test dry run exits with git's return code on failure."""
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

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1  # Git failure

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(1)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Should exit with git's failure code
                mock_exit.assert_called_with(1)

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
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock the API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message") as mock_api:
                            # Mock additional required functions
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        # Mock show_dry_run_summary to avoid actual git call
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # Verify API was called (happens before dry-run check)
                                            mock_api.assert_called_once()

                                            # Verify dry run summary was shown
                                            mock_show_summary.assert_called_once()
                                            args = mock_show_summary.call_args[0][0]
                                            assert args.dry_run is True

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
                        # Mock API to ensure it's not called when no changes
                        with patch("git_commitai.make_api_request") as mock_api:
                            # Catch the sys.exit(1) that happens when no changes
                            with patch("sys.exit") as mock_exit:
                                mock_exit.side_effect = SystemExit(1)

                                with suppress(SystemExit):
                                    git_commitai.main()

                                # API should NOT be called when no staged changes
                                mock_api.assert_not_called()

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
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # Verify auto-stage was passed through
                                            mock_show_summary.assert_called_once()
                                            args = mock_show_summary.call_args[0][0]
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
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # Dry run should work with verbose
                                            mock_show_summary.assert_called_once()
                                            args = mock_show_summary.call_args[0][0]
                                            assert args.verbose is True

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
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # Verify amend was passed through
                                            args = mock_show_summary.call_args[0][0]
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
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # Verify message was passed through
                                            args = mock_show_summary.call_args[0][0]
                                            assert args.message == "Fixed bug"

    def test_dry_run_makes_api_request(self):
        """Test that dry run makes API request before showing summary."""
        test_argv = ["git-commitai", "--dry-run"]

        with patch("sys.argv", test_argv):
            with patch("subprocess.run") as mock_subprocess:
                # Mock git repository check
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = ""
                mock_subprocess.return_value.stderr = ""

                with patch("git_commitai.check_staged_changes", return_value=True):
                    # CRITICAL FIX: Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        with patch("git_commitai.get_git_diff", return_value="diff"):
                            with patch("git_commitai.get_staged_files", return_value="files"):
                                with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                    mock_show_summary.side_effect = SystemExit(0)

                                    with patch("git_commitai.make_api_request", return_value="Test commit message") as mock_api:
                                        with patch("sys.exit") as mock_exit:
                                            mock_exit.side_effect = SystemExit(0)

                                            with suppress(SystemExit):
                                                git_commitai.main()

                                            # API request SHOULD be made (happens before dry-run check)
                                            mock_api.assert_called_once()

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
                    # Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("git_commitai.create_commit_message_file") as mock_create:
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                with suppress(SystemExit):
                                                    git_commitai.main()

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
                    # Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("git_commitai.open_editor") as mock_editor:
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                with suppress(SystemExit):
                                                    git_commitai.main()

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
                    # Properly mock get_env_config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test-api.com",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        # Mock API request
                        with patch("git_commitai.make_api_request", return_value="Test commit message"):
                            with patch("git_commitai.get_git_diff", return_value="diff"):
                                with patch("git_commitai.get_staged_files", return_value="files"):
                                    with patch("git_commitai.show_dry_run_summary") as mock_show_summary:
                                        mock_show_summary.side_effect = SystemExit(0)

                                        with patch("git_commitai.debug_log") as mock_debug:
                                            with patch("sys.exit") as mock_exit:
                                                mock_exit.side_effect = SystemExit(0)

                                                with suppress(SystemExit):
                                                    git_commitai.main()

                                                # Debug log should mention dry-run mode
                                                debug_calls = [str(call) for call in mock_debug.call_args_list]
                                                assert any("DRY RUN MODE" in str(call) or "dry-run" in str(call).lower()
                                                          for call in debug_calls)

    def test_dry_run_delegation_to_git(self):
        """Test that dry run properly delegates all work to git commit --dry-run."""
        args = argparse.Namespace(
            amend=False,
            allow_empty=False,
            no_verify=False,
            author=None,
            date=None,
            all=False,
            message="Test message",
            verbose=False,
            dry_run=True,
            debug=False,
            api_key=None,
            api_url=None,
            model=None
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("sys.exit") as mock_exit:
                mock_exit.side_effect = SystemExit(0)

                with suppress(SystemExit):
                    git_commitai.show_dry_run_summary(args)

                # Verify the exact command structure
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == "git"
                assert call_args[1] == "commit"
                assert call_args[2] == "--dry-run"
                assert "-m" in call_args

                # Check that subprocess.run was called with check=False
                assert not mock_run.call_args[1].get('check', True)
