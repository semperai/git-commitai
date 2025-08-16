"""Tests for .gitmessage template file reading functionality."""

import os
from unittest.mock import patch, mock_open
import git_commitai


class TestGitMessageTemplate:
    """Test reading and processing .gitmessage template files."""

    def test_read_repo_gitmessage_highest_priority(self):
        """Test that .gitmessage in repo root has highest priority over all others."""
        repo_content = "# Repository-specific template"
        config_content = "# Configured template via commit.template"
        home_content = "# Home directory template"

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "/path/to/configured/template"  # Config exists
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            # Mock file existence - all files exist
            def mock_isfile(path):
                return path in [
                    "/repo/root/.gitmessage",
                    "/path/to/configured/template",
                    os.path.expanduser("~/.gitmessage")
                ]

            # Mock file reading
            def mock_file_open(path, mode='r'):
                if path == "/repo/root/.gitmessage":
                    return mock_open(read_data=repo_content)()
                elif path == "/path/to/configured/template":
                    return mock_open(read_data=config_content)()
                elif path == os.path.expanduser("~/.gitmessage"):
                    return mock_open(read_data=home_content)()
                raise FileNotFoundError(f"No such file: {path}")

            with patch("os.path.isfile", side_effect=mock_isfile):
                with patch("builtins.open", side_effect=mock_file_open):
                    result = git_commitai.read_gitmessage_template()

                    # Should use repo .gitmessage even though config template exists
                    assert result == repo_content
                    assert "Repository-specific template" in result

    def test_read_configured_template_second_priority(self):
        """Test reading template configured via git config when no repo .gitmessage exists."""
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

            # Repo .gitmessage doesn't exist, but configured template does
            def mock_isfile(path):
                if path == "/repo/root/.gitmessage":
                    return False  # No repo .gitmessage
                elif path == "/path/to/template":
                    return True   # Configured template exists
                return False

            with patch("os.path.isfile", side_effect=mock_isfile):
                with patch("builtins.open", mock_open(read_data=template_content)):
                    result = git_commitai.read_gitmessage_template()

                    assert result == template_content
                    assert "feat|fix|docs" in result

    def test_read_home_gitmessage_lowest_priority(self):
        """Test reading ~/.gitmessage as last fallback."""
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
                    # The function will check in order:
                    # 1. /repo/root/.gitmessage (doesn't exist)
                    # 2. No configured template (already returned empty)
                    # 3. /home/user/.gitmessage (exists)
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
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.expanduser", return_value="/home/user/my-template"):
                with patch("os.path.isfile") as mock_isfile:
                    def isfile_side_effect(path):
                        if path == "/repo/root/.gitmessage":
                            return False  # No repo .gitmessage
                        elif path == "/home/user/my-template":
                            return True   # Expanded template exists
                        return False

                    mock_isfile.side_effect = isfile_side_effect

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
                    with patch("os.path.isfile") as mock_isfile:
                        def isfile_side_effect(path):
                            if path == "/repo/root/.gitmessage":
                                return False  # No repo .gitmessage
                            elif path == "/repo/root/.github/commit-template":
                                return True   # Relative template exists
                            return False

                        mock_isfile.side_effect = isfile_side_effect

                        with patch("builtins.open", mock_open(read_data=template_content)):
                            result = git_commitai.read_gitmessage_template()

                            assert result == template_content

    def test_template_read_error(self):
        """Test handling of file read errors."""
        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "/path/to/template"
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            with patch("os.path.isfile") as mock_isfile:
                def isfile_side_effect(path):
                    if path == "/repo/root/.gitmessage":
                        return True  # Repo .gitmessage exists but will fail to read
                    return False

                mock_isfile.side_effect = isfile_side_effect

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
                        "repo_config": {}
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
                        "repo_config": {}
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

    def test_precedence_order_comprehensive(self):
        """Test complete precedence order: repo > config > home."""
        repo_content = "# Repo template"
        configured_content = "# Configured template"
        home_content = "# Home template"

        with patch("git_commitai.run_git") as mock_run:
            def side_effect(args, check=True):
                if "config" in args and "--get" in args and "commit.template" in args:
                    return "/configured/template"
                elif "rev-parse" in args and "--show-toplevel" in args:
                    return "/repo/root"
                return ""

            mock_run.side_effect = side_effect

            # Test 1: Repo .gitmessage takes highest precedence (even when others exist)
            with patch("os.path.isfile") as mock_isfile:
                mock_isfile.return_value = True  # All files exist

                def mock_file_open(path, mode='r'):
                    if path == "/repo/root/.gitmessage":
                        return mock_open(read_data=repo_content)()
                    elif path == "/configured/template":
                        return mock_open(read_data=configured_content)()
                    elif path.endswith("/.gitmessage"):  # Home
                        return mock_open(read_data=home_content)()
                    raise FileNotFoundError(f"No such file: {path}")

                with patch("builtins.open", side_effect=mock_file_open):
                    result = git_commitai.read_gitmessage_template()
                    assert result == repo_content

            # Test 2: Configured template when no repo .gitmessage
            with patch("os.path.isfile") as mock_isfile:
                def isfile_side_effect(path):
                    if path == "/repo/root/.gitmessage":
                        return False  # No repo .gitmessage
                    elif path == "/configured/template":
                        return True   # Configured template exists
                    return False

                mock_isfile.side_effect = isfile_side_effect

                with patch("builtins.open", mock_open(read_data=configured_content)):
                    result = git_commitai.read_gitmessage_template()
                    assert result == configured_content

            # Test 3: Home template as last resort (no repo, no config)
            mock_run.side_effect = [
                "",  # No configured template
                "/repo/root"  # Git root
            ]

            with patch("os.path.expanduser") as mock_expanduser:
                mock_expanduser.return_value = "/home/user/.gitmessage"

                with patch("os.path.isfile") as mock_isfile:
                    def isfile_side_effect(path):
                        if path == "/repo/root/.gitmessage":
                            return False  # No repo .gitmessage
                        elif path == "/home/user/.gitmessage":
                            return True   # Home .gitmessage exists
                        return False

                    mock_isfile.side_effect = isfile_side_effect

                    with patch("builtins.open", mock_open(read_data=home_content)):
                        result = git_commitai.read_gitmessage_template()
                        assert result == home_content

    def test_repo_gitmessage_overrides_configured(self):
        """Test that repo .gitmessage specifically overrides commit.template setting."""
        repo_content = "# This is the repo template that should be used"
        config_content = "# This configured template should NOT be used"

        # First patch get_git_root to return a consistent value
        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            # Then patch run_git for the config check
            with patch("git_commitai.run_git") as mock_run:
                def run_git_side_effect(args, check=True):
                    if "config" in args and "--get" in args and "commit.template" in args:
                        return "/user/configured/template"
                    return ""

                mock_run.side_effect = run_git_side_effect

                # Key: patch os.path at the git_commitai module level
                # This is crucial because git_commitai imports os and uses os.path.isfile
                with patch.object(git_commitai.os.path, 'isfile') as mock_isfile:
                    # Setup isfile mock
                    def isfile_side_effect(path):
                        return path in ["/repo/root/.gitmessage", "/user/configured/template"]

                    mock_isfile.side_effect = isfile_side_effect

                    # Mock file opening
                    def mock_file_open(filename, mode='r'):
                        if filename == "/repo/root/.gitmessage":
                            return mock_open(read_data=repo_content)()
                        elif filename == "/user/configured/template":
                            return mock_open(read_data=config_content)()
                        raise FileNotFoundError(f"No such file: {filename}")

                    with patch("builtins.open", side_effect=mock_file_open):
                        result = git_commitai.read_gitmessage_template()

                        # Should use repo template, not configured one
                        assert result == repo_content
                        assert "repo template that should be used" in result
