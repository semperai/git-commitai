"""Tests for .gitmessage template file reading functionality."""

import os
import tempfile
from unittest.mock import patch, mock_open
import git_commitai


class TestGitMessageTemplate:
    """Test reading and processing .gitmessage template files."""

    def test_read_configured_template(self):
        """Test reading template configured via git config."""
        template_content = """# Type: feat|fix|docs|style|refactor|test|chore
# Scope: optional module name
# Subject: imperative mood description

# Body: explain what and why vs how"""

        with patch("git_commitai.run_git") as mock_run:
            # Mock git config to return a template path
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "/path/to/template"
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.isfile", return_value=True):
                with patch("builtins.open", mock_open(read_data=template_content)):
                    result = git_commitai.read_gitmessage_template()

                    assert result == template_content
                    assert "feat|fix|docs" in result

    def test_read_repo_gitmessage(self):
        """Test reading .gitmessage from repository root."""
        template_content = """# Project-specific commit guidelines
# Always reference issue numbers"""

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return ""  # No configured template
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.isfile") as mock_isfile:
                # First path (configured) doesn't exist, second (repo) does
                mock_isfile.side_effect = [False, True]

                with patch("builtins.open", mock_open(read_data=template_content)):
                    result = git_commitai.read_gitmessage_template()

                    assert result == template_content
                    assert "issue numbers" in result

    def test_read_home_gitmessage(self):
        """Test reading ~/.gitmessage as fallback."""
        template_content = """# Global commit template
# User preferences"""

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return ""  # No configured template
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            # Patch os.path.expanduser at the module level where it's imported
            with patch("os.path.expanduser") as mock_expanduser:
                # Make expanduser return the actual path for ~/.gitmessage
                mock_expanduser.return_value = "/home/user/.gitmessage"

                with patch("os.path.isfile") as mock_isfile:
                    # The function will check:
                    # 1. /repo/root/.gitmessage (doesn't exist)
                    # 2. /home/user/.gitmessage (exists)
                    def isfile_side_effect(path):
                        if path == "/repo/root/.gitmessage":
                            return False
                        elif path == "/home/user/.gitmessage":
                            return True
                        return False

                    mock_isfile.side_effect = isfile_side_effect

                    with patch("builtins.open", mock_open(read_data=template_content)):
                        result = git_commitai.read_gitmessage_template()

                        assert result == template_content
                        assert "Global commit template" in result

    def test_no_gitmessage_found(self):
        """Test when no .gitmessage file exists."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = ""  # No configured template

            with patch("os.path.isfile", return_value=False):
                result = git_commitai.read_gitmessage_template()

                assert result is None

    def test_template_with_tilde_expansion(self):
        """Test expanding ~ in configured template path."""
        template_content = "# Template from home"

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "~/my-template"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.expanduser", return_value="/home/user/my-template"):
                with patch("os.path.isfile", return_value=True):
                    with patch("builtins.open", mock_open(read_data=template_content)):
                        result = git_commitai.read_gitmessage_template()

                        assert result == template_content

    def test_template_relative_path(self):
        """Test resolving relative template path from git root."""
        template_content = "# Relative template"

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return ".github/commit-template"
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.isabs", return_value=False):
                with patch("os.path.join", return_value="/repo/root/.github/commit-template"):
                    with patch("os.path.isfile", return_value=True):
                        with patch("builtins.open", mock_open(read_data=template_content)):
                            result = git_commitai.read_gitmessage_template()

                            assert result == template_content

    def test_template_read_error(self):
        """Test handling of file read errors."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "/path/to/template"

            with patch("os.path.isfile", return_value=True):
                with patch("builtins.open", side_effect=IOError("Permission denied")):
                    result = git_commitai.read_gitmessage_template()

                    assert result is None

    def test_get_git_root(self):
        """Test getting git repository root."""
        with patch("git_commitai.run_git") as mock_run:
            mock_run.return_value = "/repo/root"

            result = git_commitai.get_git_root()

            assert result == "/repo/root"
            mock_run.assert_called_once_with(["rev-parse", "--show-toplevel"])

    def test_get_git_root_fallback(self):
        """Test git root fallback to current directory."""
        with patch("git_commitai.run_git", side_effect=Exception("Not a git repo")):
            with patch("os.getcwd", return_value="/current/dir"):
                result = git_commitai.get_git_root()

                assert result == "/current/dir"

    def test_template_in_prompt_context(self):
        """Test that template content is added to the prompt correctly."""
        template_content = """# Commit format:
# type(scope): subject
#
# Types: feat, fix, docs, style, refactor, test, chore"""

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test-key",
                        "api_url": "http://test-api",
                        "model": "test-model",
                    }

                    with patch("git_commitai.read_gitmessage_template", return_value=template_content):
                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "feat: Add new feature"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                    with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                        with patch("git_commitai.open_editor"):
                                            with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()

                                                        # Verify the template was included in the prompt
                                                        call_args = mock_api.call_args[0]
                                                        prompt = call_args[1]

                                                        assert "PROJECT-SPECIFIC COMMIT TEMPLATE/GUIDELINES:" in prompt
                                                        assert template_content in prompt
                                                        assert "type(scope): subject" in prompt

    def test_template_not_in_prompt_when_missing(self):
        """Test that prompt works normally when no template exists."""
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.get_env_config") as mock_config:
                    mock_config.return_value = {
                        "api_key": "test-key",
                        "api_url": "http://test-api",
                        "model": "test-model",
                    }

                    with patch("git_commitai.read_gitmessage_template", return_value=None):
                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "Fix authentication bug"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                    with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                        with patch("git_commitai.open_editor"):
                                            with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                    with patch("sys.argv", ["git-commitai"]):
                                                        git_commitai.main()

                                                        # Verify the template section is NOT in the prompt
                                                        call_args = mock_api.call_args[0]
                                                        prompt = call_args[1]

                                                        assert "PROJECT-SPECIFIC COMMIT TEMPLATE/GUIDELINES:" not in prompt

    def test_precedence_order(self):
        """Test that template precedence order is correct."""
        configured_content = "# Configured template"
        repo_content = "# Repo template"
        home_content = "# Home template"

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "/configured/template"
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            # Test 1: Configured template takes precedence
            with patch("os.path.isfile", return_value=True):
                with patch("builtins.open", mock_open(read_data=configured_content)):
                    result = git_commitai.read_gitmessage_template()
                    assert result == configured_content

            # Test 2: Repo template when no configured template
            mock_run.side_effect = [
                "",  # No configured template
                "/repo/root"  # Git root
            ]

            with patch("os.path.isfile") as mock_isfile:
                # First check will be for /repo/root/.gitmessage
                mock_isfile.side_effect = [True]  # Repo .gitmessage exists

                with patch("builtins.open", mock_open(read_data=repo_content)):
                    result = git_commitai.read_gitmessage_template()
                    assert result == repo_content

            # Test 3: Home template as last resort
            mock_run.side_effect = [
                "",  # No configured template
                "/repo/root"  # Git root
            ]

            with patch("os.path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = "/home/user/.gitmessage"

                with patch("os.path.isfile") as mock_isfile:
                    # Check sequence: repo doesn't exist, home exists
                    def isfile_side_effect(path):
                        if path == "/repo/root/.gitmessage":
                            return False
                        elif path == "/home/user/.gitmessage":
                            return True
                        return False

                    mock_isfile.side_effect = isfile_side_effect

                    with patch("builtins.open", mock_open(read_data=home_content)):
                        result = git_commitai.read_gitmessage_template()
                        assert result == home_content
