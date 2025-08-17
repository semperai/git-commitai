"""Tests for --date flag functionality."""

import tempfile
import subprocess
from unittest.mock import patch, MagicMock
import git_commitai


class TestDateFeatures:
    """Test --date specific features."""

    def test_build_ai_prompt_with_date(self):
        """Test that AI prompt includes date information."""
        args = MagicMock()
        args.message = "test context"
        args.amend = False
        args.all = False
        args.no_verify = False

        repo_config = {}
        date = "2024-01-15 14:30:00"

        prompt = git_commitai.build_ai_prompt(
            repo_config, args, allow_empty=False, author=None, date=date
        )

        assert "Using custom date: 2024-01-15 14:30:00" in prompt
        assert "Note: Using custom date" in prompt

    def test_build_ai_prompt_with_date_custom_template(self):
        """Test that custom template properly replaces {DATE_NOTE} placeholder."""
        args = MagicMock()
        args.message = None
        args.amend = False
        args.all = False
        args.no_verify = False

        repo_config = {
            'prompt_template': """Custom template for testing.
            {DATE_NOTE}
            {CONTEXT}
            Generate a commit message:"""
        }
        date = "2024-12-25T12:00:00"

        prompt = git_commitai.build_ai_prompt(
            repo_config, args, allow_empty=False, author=None, date=date
        )

        assert "Using custom date: 2024-12-25T12:00:00" in prompt
        assert "{DATE_NOTE}" not in prompt  # Should be replaced

    def test_create_commit_message_file_with_date(self):
        """Test creating commit message file with date information."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git", return_value="M\tfile.txt"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Test commit message",
                        date="2024-01-01 00:00:00"
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Test commit message" in content
                    assert "# Using custom date: 2024-01-01 00:00:00" in content

    def test_successful_commit_with_date(self):
        """Test successful commit flow with --date flag."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--date", "2024-06-15 10:30:00"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with --date
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any("--date" in c.args[0] and "2024-06-15 10:30:00" in c.args[0] for c in commit_calls)

    def test_date_various_formats(self):
        """Test that different date formats are accepted."""
        test_cases = [
            "2024-01-15T14:30:00",  # ISO 8601
            "2024-01-15 14:30:00",  # Simple format
            "@1705329000",  # Unix timestamp
            "2 days ago",  # Relative time
            "last week",  # Relative time
            "Mon, 15 Jan 2024 14:30:00 +0000",  # RFC 2822
            "yesterday",  # Relative
            "now",  # Current time
        ]

        for date in test_cases:
            args = MagicMock()
            args.message = None
            args.amend = False
            args.all = False
            args.no_verify = False

            prompt = git_commitai.build_ai_prompt(
                {}, args, allow_empty=False, author=None, date=date
            )

            assert f"Using custom date: {date}" in prompt

    def test_date_with_amend(self):
        """Test --date flag combined with --amend."""
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

                    with patch("git_commitai.make_api_request", return_value="Amended commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--amend", "--date", "@1705329000"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both --amend and --date
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--amend" in c.args[0] and
                                                        "--date" in c.args[0] and
                                                        "@1705329000" in c.args[0]
                                                        for c in commit_calls
                                                    )

    def test_date_in_commit_message_comments(self):
        """Test that date information appears in commit message editor comments."""
        with patch("git_commitai.get_current_branch", return_value="feature"):
            with patch("git_commitai.run_git", return_value=""):
                with tempfile.TemporaryDirectory() as tmpdir:
                    date = "2024-12-31 23:59:59"
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Year end commit",
                        date=date,
                        verbose=True  # Enable verbose to see more comments
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check that date info is in comments
                    assert f"# Using custom date: {date}" in content
                    # Check that it comes before the branch info
                    date_pos = content.index(f"# Using custom date: {date}")
                    branch_pos = content.index("# On branch feature")
                    assert date_pos < branch_pos

    def test_author_and_date_combined(self):
        """Test --author and --date flags used together."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--author", "Test <test@example.com>", "--date", "2 weeks ago"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both flags
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--author" in c.args[0] and
                                                        "Test <test@example.com>" in c.args[0] and
                                                        "--date" in c.args[0] and
                                                        "2 weeks ago" in c.args[0]
                                                        for c in commit_calls
                                                    )

    def test_date_with_allow_empty(self):
        """Test --date with --allow-empty flag."""
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

                    with patch("git_commitai.make_api_request", return_value="Empty commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "--allow-empty", "--date", "yesterday"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both flags
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--allow-empty" in c.args[0] and
                                                        "--date" in c.args[0] and
                                                        "yesterday" in c.args[0]
                                                        for c in commit_calls
                                                    )

    def test_date_with_no_verify(self):
        """Test --date with --no-verify flag."""
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

                    with patch("git_commitai.make_api_request", return_value="Test commit"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", ["git-commitai", "-n", "--date", "now"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both flags
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--no-verify" in c.args[0] and
                                                        "--date" in c.args[0] and
                                                        "now" in c.args[0]
                                                        for c in commit_calls
                                                    )

    def test_build_ai_prompt_with_both_author_and_date(self):
        """Test that AI prompt includes both author and date when both are provided."""
        args = MagicMock()
        args.message = None
        args.amend = False
        args.all = False
        args.no_verify = False

        repo_config = {}
        author = "CI Bot <ci@example.com>"
        date = "2024-03-15T10:00:00"

        prompt = git_commitai.build_ai_prompt(
            repo_config, args, allow_empty=False, author=author, date=date
        )

        assert f"Using custom author: {author}" in prompt
        assert f"Using custom date: {date}" in prompt
