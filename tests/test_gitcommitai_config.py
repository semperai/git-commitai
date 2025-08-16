"""Tests for .gitcommitai configuration file functionality."""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO

import git_commitai


class TestLoadGitCommitAIConfig:
    """Test loading and parsing .gitcommitai configuration files."""

    def test_no_config_file(self):
        """Test when no .gitcommitai file exists."""
        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=False):
                config = git_commitai.load_gitcommitai_config()
                assert config == {}

    def test_simple_template_only(self):
        """Test loading a simple template without model specification."""
        template_content = """You are a commit message generator.

Follow these rules:
- Use conventional commits
- Be concise

Changes: {DIFF}
Files: {FILES}

Generate a commit message:"""

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=template_content)):
                    config = git_commitai.load_gitcommitai_config()

                    assert "prompt_template" in config
                    assert config["prompt_template"] == template_content.strip()
                    assert "model" not in config

    def test_template_with_model(self):
        """Test loading template with model specification."""
        content = """model: gpt-4

You are an expert commit message generator.

Use these conventions:
- Angular style commits
- Reference JIRA tickets

Context: {CONTEXT}
Changes: {DIFF}

Generate message:"""

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=content)):
                    config = git_commitai.load_gitcommitai_config()

                    assert config["model"] == "gpt-4"
                    assert "prompt_template" in config
                    assert "Angular style commits" in config["prompt_template"]
                    assert "model: gpt-4" not in config["prompt_template"]  # Model line should be removed

    def test_model_with_colon_separator(self):
        """Test model specification with colon separator."""
        content = """model: claude-3-opus
Template content here"""

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=content)):
                    config = git_commitai.load_gitcommitai_config()

                    assert config["model"] == "claude-3-opus"

    def test_model_with_equals_separator(self):
        """Test model specification with equals separator."""
        content = """model=gpt-4-turbo
Template content here"""

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=content)):
                    config = git_commitai.load_gitcommitai_config()

                    assert config["model"] == "gpt-4-turbo"

    def test_json_format_backward_compatibility(self):
        """Test backward compatibility with JSON format."""
        json_config = {
            "model": "gpt-3.5-turbo",
            "prompt": "Custom prompt template with {DIFF} and {FILES}"
        }

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(json_config))):
                    config = git_commitai.load_gitcommitai_config()

                    assert config["model"] == "gpt-3.5-turbo"
                    assert config["prompt_template"] == json_config["prompt"]

    def test_json_without_prompt(self):
        """Test JSON config without prompt field."""
        json_config = {
            "model": "gpt-4",
            "some_other_field": "value"
        }

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json.dumps(json_config))):
                    config = git_commitai.load_gitcommitai_config()

                    assert config["model"] == "gpt-4"
                    assert "prompt_template" not in config

    def test_invalid_json_treated_as_template(self):
        """Test that invalid JSON is treated as a template."""
        content = """{This is not valid JSON}
But it's a valid template with {DIFF}"""

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=content)):
                    config = git_commitai.load_gitcommitai_config()

                    assert "prompt_template" in config
                    assert "{DIFF}" in config["prompt_template"]

    def test_file_read_error(self):
        """Test handling of file read errors."""
        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", side_effect=IOError("Permission denied")):
                    config = git_commitai.load_gitcommitai_config()
                    assert config == {}

    def test_git_root_error(self):
        """Test handling when git root cannot be determined."""
        with patch("git_commitai.get_git_root", side_effect=Exception("Not a git repo")):
            config = git_commitai.load_gitcommitai_config()
            assert config == {}

    def test_empty_file(self):
        """Test loading an empty .gitcommitai file."""
        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="")):
                    config = git_commitai.load_gitcommitai_config()
                    assert config == {}

    def test_whitespace_only_file(self):
        """Test loading a file with only whitespace."""
        content = "   \n\n\t\n   "

        with patch("git_commitai.get_git_root", return_value="/repo/root"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=content)):
                    config = git_commitai.load_gitcommitai_config()
                    assert config == {}


class TestBuildAIPrompt:
    """Test building AI prompts with template substitution."""

    def test_default_prompt_no_config(self):
        """Test using default prompt when no config exists."""
        repo_config = {}
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        assert "You are a git commit message generator" in prompt
        assert "CRITICAL RULES YOU MUST FOLLOW" in prompt
        assert "imperative mood" in prompt

    def test_custom_template_basic(self):
        """Test using a custom template with basic placeholders."""
        repo_config = {
            "prompt_template": "Custom prompt\n{CONTEXT}\n{DIFF}\n{FILES}"
        }
        mock_args = MagicMock()
        mock_args.message = "Added new feature"
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        assert "Custom prompt" in prompt
        assert "Additional context from user: Added new feature" in prompt
        # Note: {DIFF} and {FILES} are not replaced in build_ai_prompt,
        # they're handled later in main()

    def test_template_with_gitmessage(self):
        """Test template with GITMESSAGE placeholder."""
        repo_config = {
            "prompt_template": "Project rules:\n{GITMESSAGE}\n\nGenerate commit:"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = False

        with patch("git_commitai.read_gitmessage_template", return_value="# Use conventional commits"):
            prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

            assert "Project rules:" in prompt
            assert "# Use conventional commits" in prompt

    def test_template_with_amend_note(self):
        """Test template with AMEND_NOTE placeholder."""
        repo_config = {
            "prompt_template": "Instructions:\n{AMEND_NOTE}\nGenerate message:"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = True
        mock_args.all = False
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        assert "Note: You are amending the previous commit." in prompt

    def test_template_with_auto_stage_note(self):
        """Test template with AUTO_STAGE_NOTE placeholder."""
        repo_config = {
            "prompt_template": "{AUTO_STAGE_NOTE}\nGenerate message:"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = True
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        assert "Note: Files were automatically staged using the -a flag." in prompt

    def test_template_with_no_verify_note(self):
        """Test template with NO_VERIFY_NOTE placeholder."""
        repo_config = {
            "prompt_template": "{NO_VERIFY_NOTE}\nGenerate message:"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = True

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        assert "Note: Git hooks will be skipped for this commit (--no-verify)." in prompt

    def test_template_with_allow_empty_note(self):
        """Test template with ALLOW_EMPTY_NOTE placeholder."""
        repo_config = {
            "prompt_template": "{ALLOW_EMPTY_NOTE}\nGenerate message:"
        }
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=True)

        assert "Note: This is an empty commit with no changes (--allow-empty)" in prompt
        assert "Generate a message explaining why this empty commit is being created" in prompt

    def test_template_with_all_placeholders(self):
        """Test template with all placeholders."""
        repo_config = {
            "prompt_template": """Context: {CONTEXT}
Git message: {GITMESSAGE}
{AMEND_NOTE}
{AUTO_STAGE_NOTE}
{NO_VERIFY_NOTE}
{ALLOW_EMPTY_NOTE}
Diff: {DIFF}
Files: {FILES}"""
        }
        mock_args = MagicMock()
        mock_args.message = "Bug fix"
        mock_args.amend = True
        mock_args.all = True
        mock_args.no_verify = True

        with patch("git_commitai.read_gitmessage_template", return_value="Template content"):
            prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=True)

            assert "Additional context from user: Bug fix" in prompt
            assert "Template content" in prompt
            assert "amending the previous commit" in prompt
            assert "automatically staged" in prompt
            assert "hooks will be skipped" in prompt
            assert "empty commit" in prompt

    def test_template_with_unused_placeholders(self):
        """Test that unused placeholders are replaced with empty strings."""
        repo_config = {
            "prompt_template": "Start\n{CONTEXT}\n{AMEND_NOTE}\nEnd"
        }
        mock_args = MagicMock()
        mock_args.message = None  # No context
        mock_args.amend = False  # No amend
        mock_args.all = False
        mock_args.no_verify = False

        prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

        # Unused placeholders should be replaced with empty strings
        assert "{CONTEXT}" not in prompt
        assert "{AMEND_NOTE}" not in prompt
        assert "Start" in prompt
        assert "End" in prompt

    def test_default_prompt_with_gitmessage(self):
        """Test default prompt includes .gitmessage when no custom template."""
        repo_config = {}  # No custom template
        mock_args = MagicMock()
        mock_args.message = None
        mock_args.amend = False
        mock_args.all = False
        mock_args.no_verify = False

        with patch("git_commitai.read_gitmessage_template", return_value="# Commit guidelines"):
            prompt = git_commitai.build_ai_prompt(repo_config, mock_args, allow_empty=False)

            assert "PROJECT-SPECIFIC COMMIT TEMPLATE/GUIDELINES:" in prompt
            assert "# Commit guidelines" in prompt


class TestEnvConfigWithGitCommitAI:
    """Test environment configuration with .gitcommitai integration."""

    def test_config_precedence_cli_overrides_all(self):
        """Test that CLI arguments override everything."""
        mock_args = MagicMock()
        mock_args.api_key = "cli-key"
        mock_args.api_url = "https://cli-api.com"
        mock_args.model = "cli-model"

        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            with patch("git_commitai.load_gitcommitai_config", return_value={"model": "repo-model"}):
                config = git_commitai.get_env_config(mock_args)

                assert config["api_key"] == "cli-key"
                assert config["api_url"] == "https://cli-api.com"
                assert config["model"] == "cli-model"

    def test_config_precedence_env_overrides_repo(self):
        """Test that environment variables override repo config."""
        mock_args = MagicMock()
        mock_args.api_key = None
        mock_args.api_url = None
        mock_args.model = None

        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            with patch("git_commitai.load_gitcommitai_config", return_value={"model": "repo-model"}):
                config = git_commitai.get_env_config(mock_args)

                assert config["api_key"] == "env-key"
                assert config["model"] == "env-model"

    def test_config_uses_repo_when_no_env(self):
        """Test that repo config is used when no env vars."""
        mock_args = MagicMock()
        mock_args.api_key = None
        mock_args.api_url = None
        mock_args.model = None

        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "test-key"}, clear=True):
            with patch("git_commitai.load_gitcommitai_config", return_value={"model": "repo-model"}):
                config = git_commitai.get_env_config(mock_args)

                assert config["model"] == "repo-model"

    def test_config_defaults_when_nothing_set(self):
        """Test default values when nothing is configured."""
        mock_args = MagicMock()
        mock_args.api_key = None
        mock_args.api_url = None
        mock_args.model = None

        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "test-key"}):
            with patch("git_commitai.load_gitcommitai_config", return_value={}):
                config = git_commitai.get_env_config(mock_args)

                assert config["api_url"] == "https://openrouter.ai/api/v1/chat/completions"
                assert config["model"] == "qwen/qwen3-coder"

    def test_repo_config_attached(self):
        """Test that repo_config is attached to main config."""
        mock_args = MagicMock()
        mock_args.api_key = None
        mock_args.api_url = None
        mock_args.model = None

        repo_config = {
            "model": "gpt-4",
            "prompt_template": "Custom template"
        }

        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "test-key"}):
            with patch("git_commitai.load_gitcommitai_config", return_value=repo_config):
                config = git_commitai.get_env_config(mock_args)

                assert "repo_config" in config
                assert config["repo_config"] == repo_config
                assert config["repo_config"]["prompt_template"] == "Custom template"


class TestMainFlowWithGitCommitAI:
    """Test main flow with .gitcommitai configuration."""

    def test_main_with_custom_template(self):
        """Test main flow using custom template from .gitcommitai."""
        custom_template = """You are a specialized commit message generator.

Rules: {CONTEXT}

Changes to review:
{DIFF}

Files:
{FILES}

Generate commit message:"""

        repo_config = {
            "model": "gpt-4",
            "prompt_template": custom_template
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.load_gitcommitai_config", return_value=repo_config):
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test",
                            "model": "gpt-4",
                            "repo_config": repo_config
                        }

                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "feat: Add new feature"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.get_git_diff", return_value="diff content"):
                                    with patch("git_commitai.get_staged_files", return_value="file content"):
                                        with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                            with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                                with patch("git_commitai.open_editor"):
                                                    with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                        with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                            with patch("sys.argv", ["git-commitai", "-m", "Added feature"]):
                                                                git_commitai.main()

                                                                # Verify the custom template was used
                                                                call_args = mock_api.call_args[0]
                                                                prompt = call_args[1]

                                                                assert "You are a specialized commit message generator" in prompt
                                                                assert "diff content" in prompt  # {DIFF} replaced
                                                                assert "file content" in prompt  # {FILES} replaced
                                                                assert "Added feature" in prompt  # Context included

    def test_main_with_template_placeholders_replaced(self):
        """Test that template placeholders are properly replaced in main flow."""
        custom_template = "Review: {DIFF}\nFiles: {FILES}\nGenerate:"

        repo_config = {"prompt_template": custom_template}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.load_gitcommitai_config", return_value=repo_config):
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test",
                            "model": "test-model",
                            "repo_config": repo_config
                        }

                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "fix: Fix bug"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.get_git_diff", return_value="```\ndiff --git a/file.py\n```"):
                                    with patch("git_commitai.get_staged_files", return_value="file.py\n```\ncode\n```"):
                                        with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                            with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                                with patch("git_commitai.open_editor"):
                                                    with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                        with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                            with patch("sys.argv", ["git-commitai"]):
                                                                git_commitai.main()

                                                                # Verify placeholders were replaced
                                                                call_args = mock_api.call_args[0]
                                                                prompt = call_args[1]

                                                                assert "{DIFF}" not in prompt
                                                                assert "{FILES}" not in prompt
                                                                assert "diff --git" in prompt
                                                                assert "file.py" in prompt

    def test_main_without_custom_template(self):
        """Test main flow without custom template uses default."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.load_gitcommitai_config", return_value={}):  # No custom config
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test",
                            "model": "test-model",
                            "repo_config": {}
                        }

                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "Initial commit"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.get_git_diff", return_value="diff"):
                                    with patch("git_commitai.get_staged_files", return_value="files"):
                                        with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                            with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                                with patch("git_commitai.open_editor"):
                                                    with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                        with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                            with patch("sys.argv", ["git-commitai"]):
                                                                git_commitai.main()

                                                                # Verify default prompt was used
                                                                call_args = mock_api.call_args[0]
                                                                prompt = call_args[1]

                                                                assert "You are a git commit message generator" in prompt
                                                                assert "CRITICAL RULES YOU MUST FOLLOW" in prompt

    def test_template_without_placeholders_appends_diff_files(self):
        """Test that templates without {DIFF}/{FILES} placeholders get them appended."""
        custom_template = "Simple template without placeholders"
        repo_config = {"prompt_template": custom_template}

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch("git_commitai.load_gitcommitai_config", return_value=repo_config):
                    with patch("git_commitai.get_env_config") as mock_env_config:
                        mock_env_config.return_value = {
                            "api_key": "test-key",
                            "api_url": "http://test",
                            "model": "test-model",
                            "repo_config": repo_config
                        }

                        with patch("git_commitai.make_api_request") as mock_api:
                            mock_api.return_value = "commit message"

                            with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                                with patch("git_commitai.get_git_diff", return_value="diff content"):
                                    with patch("git_commitai.get_staged_files", return_value="file content"):
                                        with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                            with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                                with patch("git_commitai.open_editor"):
                                                    with patch("git_commitai.is_commit_message_empty", return_value=False):
                                                        with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                            with patch("sys.argv", ["git-commitai"]):
                                                                git_commitai.main()

                                                                # Verify diff and files were appended
                                                                call_args = mock_api.call_args[0]
                                                                prompt = call_args[1]

                                                                assert "Simple template without placeholders" in prompt
                                                                assert "Here is the git diff of changes:" in prompt
                                                                assert "diff content" in prompt
                                                                assert "Here are all the modified files" in prompt
                                                                assert "file content" in prompt
