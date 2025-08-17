"""Tests for --author flag functionality."""

import tempfile
import subprocess
from unittest.mock import patch, MagicMock
import git_commitai


class TestAuthorFeatures:
    """Test --author specific features."""

    def test_build_ai_prompt_with_author(self):
        """Test that AI prompt includes author information."""
        args = MagicMock()
        args.message = "test context"
        args.amend = False
        args.all = False
        args.no_verify = False

        repo_config = {}
        author = "John Doe <john@example.com>"

        prompt = git_commitai.build_ai_prompt(
            repo_config, args, allow_empty=False, author=author, date=None
        )

        assert "Using custom author: John Doe <john@example.com>" in prompt
        assert "Note: Using custom author" in prompt

    def test_build_ai_prompt_with_author_custom_template(self):
        """Test that custom template properly replaces {AUTHOR_NOTE} placeholder."""
        args = MagicMock()
        args.message = None
        args.amend = False
        args.all = False
        args.no_verify = False

        repo_config = {
            'prompt_template': """Custom template for testing.
            {AUTHOR_NOTE}
            {CONTEXT}
            Generate a commit message:"""
        }
        author = "Jane Smith <jane@example.com>"

        prompt = git_commitai.build_ai_prompt(
            repo_config, args, allow_empty=False, author=author, date=None
        )

        assert "Using custom author: Jane Smith <jane@example.com>" in prompt
        assert "{AUTHOR_NOTE}" not in prompt  # Should be replaced

    def test_create_commit_message_file_with_author(self):
        """Test creating commit message file with author information."""
        with patch("git_commitai.get_current_branch", return_value="main"):
            with patch("git_commitai.run_git", return_value="M\tfile.txt"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Test commit message",
                        author="Bob Developer <bob@dev.com>"
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    assert "Test commit message" in content
                    assert "# Using custom author: Bob Developer <bob@dev.com>" in content

    def test_successful_commit_with_author(self):
        """Test successful commit flow with --author flag."""
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
                                                with patch("sys.argv", ["git-commitai", "--author", "Test User <test@example.com>"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with --author
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any("--author" in c.args[0] and "Test User <test@example.com>" in c.args[0] for c in commit_calls)

    def test_author_various_formats(self):
        """Test that different author formats are accepted."""
        test_cases = [
            "John Doe <john@example.com>",  # Full format
            "<john@example.com>",  # Email only
            "John Doe",  # Name only
            "John O'Brien <john@example.com>",  # Name with apostrophe
            "José García <jose@example.com>",  # Unicode characters
        ]

        for author in test_cases:
            args = MagicMock()
            args.message = None
            args.amend = False
            args.all = False
            args.no_verify = False

            prompt = git_commitai.build_ai_prompt(
                {}, args, allow_empty=False, author=author, date=None
            )

            assert f"Using custom author: {author}" in prompt

    def test_author_with_amend(self):
        """Test --author flag combined with --amend."""
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
                                                with patch("sys.argv", ["git-commitai", "--amend", "--author", "New Author <new@example.com>"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both --amend and --author
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--amend" in c.args[0] and
                                                        "--author" in c.args[0] and
                                                        "New Author <new@example.com>" in c.args[0]
                                                        for c in commit_calls
                                                    )

    def test_author_in_commit_message_comments(self):
        """Test that author information appears in commit message editor comments."""
        with patch("git_commitai.get_current_branch", return_value="feature"):
            with patch("git_commitai.run_git", return_value=""):
                with tempfile.TemporaryDirectory() as tmpdir:
                    author = "CI Bot <ci@automated.com>"
                    commit_file = git_commitai.create_commit_message_file(
                        tmpdir,
                        "Automated commit",
                        author=author,
                        verbose=True  # Enable verbose to see more comments
                    )

                    with open(commit_file, "r") as f:
                        content = f.read()

                    # Check that author info is in comments
                    assert f"# Using custom author: {author}" in content
                    # Check that it comes before the branch info
                    author_pos = content.index(f"# Using custom author: {author}")
                    branch_pos = content.index("# On branch feature")
                    assert author_pos < branch_pos

    def test_author_with_allow_empty(self):
        """Test --author with --allow-empty flag."""
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
                                                with patch("sys.argv", ["git-commitai", "--allow-empty", "--author", "Bot <bot@ci.com>"]):
                                                    git_commitai.main()

                                                    # Verify git commit was called with both flags
                                                    calls = [c for c in mock_run.call_args_list if c.args and isinstance(c.args[0], list)]
                                                    commit_calls = [c for c in calls if "commit" in c.args[0]]
                                                    assert any(
                                                        "--allow-empty" in c.args[0] and
                                                        "--author" in c.args[0] and
                                                        "Bot <bot@ci.com>" in c.args[0]
                                                        for c in commit_calls
                                                    )
