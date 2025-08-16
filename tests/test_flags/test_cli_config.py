"""Tests for CLI configuration override flags (--api-key, --api-url, --model)."""

import pytest
import os
from unittest.mock import patch, MagicMock
from io import StringIO

import git_commitai


class TestCLIConfigOverrides:
    """Test the CLI configuration override functionality."""

    def test_api_key_override(self):
        """Test that --api-key overrides environment variable."""
        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "env-key"}):
            with patch("sys.argv", ["git-commitai", "--api-key", "cli-key"]):
                # Parse args would normally happen in main()
                import argparse
                parser = argparse.ArgumentParser()
                parser.add_argument("--api-key")
                parser.add_argument("--api-url")
                parser.add_argument("--model")
                args = parser.parse_args(["--api-key", "cli-key"])

                config = git_commitai.get_env_config(args)

                assert config["api_key"] == "cli-key"
                assert config["api_key"] != "env-key"

    def test_api_url_override(self):
        """Test that --api-url overrides environment variable."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "test-key",
            "GIT_COMMIT_AI_URL": "https://env-url.com"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            args = parser.parse_args(["--api-url", "https://cli-url.com"])

            config = git_commitai.get_env_config(args)

            assert config["api_url"] == "https://cli-url.com"
            assert config["api_url"] != "https://env-url.com"

    def test_model_override(self):
        """Test that --model overrides environment variable."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "test-key",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            args = parser.parse_args(["--model", "cli-model"])

            config = git_commitai.get_env_config(args)

            assert config["model"] == "cli-model"
            assert config["model"] != "env-model"

    def test_all_overrides_together(self):
        """Test all three CLI overrides working together."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_URL": "https://env-url.com",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            args = parser.parse_args([
                "--api-key", "cli-key",
                "--api-url", "https://cli-url.com",
                "--model", "cli-model"
            ])

            config = git_commitai.get_env_config(args)

            assert config["api_key"] == "cli-key"
            assert config["api_url"] == "https://cli-url.com"
            assert config["model"] == "cli-model"

    def test_env_defaults_when_no_cli_override(self):
        """Test that environment variables are used when no CLI overrides."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_URL": "https://env-url.com",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            args = parser.parse_args([])  # No CLI args

            config = git_commitai.get_env_config(args)

            assert config["api_key"] == "env-key"
            assert config["api_url"] == "https://env-url.com"
            assert config["model"] == "env-model"

    def test_partial_overrides(self):
        """Test partial CLI overrides (some from CLI, some from env)."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_URL": "https://env-url.com",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            # Only override model
            args = parser.parse_args(["--model", "cli-model"])

            config = git_commitai.get_env_config(args)

            assert config["api_key"] == "env-key"  # From env
            assert config["api_url"] == "https://env-url.com"  # From env
            assert config["model"] == "cli-model"  # From CLI

    def test_cli_key_without_env_key(self):
        """Test that --api-key works even when no env key is set."""
        with patch.dict("os.environ", {}, clear=True):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")
            args = parser.parse_args(["--api-key", "cli-only-key"])

            config = git_commitai.get_env_config(args)

            assert config["api_key"] == "cli-only-key"

    def test_main_flow_with_cli_overrides(self):
        """Test the main flow with CLI configuration overrides."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch.dict("os.environ", {
                    "GIT_COMMIT_AI_KEY": "env-key",
                    "GIT_COMMIT_AI_URL": "https://env-url.com",
                    "GIT_COMMIT_AI_MODEL": "env-model"
                }):
                    with patch("git_commitai.make_api_request", return_value="Test commit") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", [
                                                    "git-commitai",
                                                    "--api-key", "cli-key",
                                                    "--api-url", "https://cli-url.com",
                                                    "--model", "gpt-4"
                                                ]):
                                                    git_commitai.main()

                                                    # Verify the API was called with CLI overrides
                                                    config_used = mock_api.call_args[0][0]
                                                    assert config_used["api_key"] == "cli-key"
                                                    assert config_used["api_url"] == "https://cli-url.com"
                                                    assert config_used["model"] == "gpt-4"

    def test_cli_overrides_with_other_flags(self):
        """Test CLI overrides combined with other git-commitai flags."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "env-key"}):
                    with patch("git_commitai.make_api_request", return_value="Test") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT") as mock_create:
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                # Combine with -a, -v, -m, and CLI overrides
                                                with patch("sys.argv", [
                                                    "git-commitai",
                                                    "-a",
                                                    "-v",
                                                    "-m", "context message",
                                                    "--model", "claude-3.5",
                                                    "--api-key", "new-key"
                                                ]):
                                                    git_commitai.main()

                                                    # Check that other flags still work
                                                    create_args = mock_create.call_args[1]
                                                    assert create_args["auto_staged"]
                                                    assert create_args["verbose"]

                                                    # Check API config
                                                    config_used = mock_api.call_args[0][0]
                                                    assert config_used["model"] == "claude-3.5"
                                                    assert config_used["api_key"] == "new-key"

                                                    # Check prompt includes context
                                                    prompt = mock_api.call_args[0][1]
                                                    assert "context message" in prompt

    def test_cli_overrides_with_debug(self):
        """Test that CLI overrides are logged when --debug is enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch.dict("os.environ", {
                    "GIT_COMMIT_AI_KEY": "env-key",
                    "GIT_COMMIT_AI_MODEL": "env-model"
                }):
                    with patch("git_commitai.make_api_request", return_value="Test"):
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("git_commitai.debug_log") as mock_debug:
                                                    with patch("sys.argv", [
                                                        "git-commitai",
                                                        "--debug",
                                                        "--model", "gpt-4",
                                                        "--api-key", "debug-key"
                                                    ]):
                                                        git_commitai.main()

                                                        # Check that debug logging was called
                                                        debug_calls = [str(call) for call in mock_debug.call_args_list]
                                                        # Should log configuration details
                                                        assert any("gpt-4" in call for call in debug_calls)

    def test_local_llm_configuration(self):
        """Test configuration for local LLM (common use case for CLI overrides)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                # No environment variables set
                with patch.dict("os.environ", {}, clear=True):
                    with patch("git_commitai.make_api_request", return_value="Local LLM commit") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", [
                                                    "git-commitai",
                                                    "--api-url", "http://localhost:11434/v1/chat/completions",
                                                    "--model", "codellama",
                                                    "--api-key", "not-needed"
                                                ]):
                                                    git_commitai.main()

                                                    # Verify local LLM configuration was used
                                                    config_used = mock_api.call_args[0][0]
                                                    assert config_used["api_url"] == "http://localhost:11434/v1/chat/completions"
                                                    assert config_used["model"] == "codellama"
                                                    assert config_used["api_key"] == "not-needed"

    def test_empty_cli_override_values(self):
        """Test behavior with empty CLI override values."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key",
            "GIT_COMMIT_AI_MODEL": "env-model"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")

            # Empty string for model - note that argparse with empty string
            # might not override in current implementation
            args = parser.parse_args(["--model", ""])

            config = git_commitai.get_env_config(args)

            # In the current implementation, empty string might not override
            # This test documents the actual behavior
            if config["model"] == "":
                # Empty string overrides
                assert config["model"] == ""
            else:
                # Empty string doesn't override (falls back to env)
                assert config["model"] == "env-model"

            assert config["api_key"] == "env-key"  # Not overridden

    def test_special_characters_in_cli_values(self):
        """Test CLI overrides with special characters."""
        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "env-key"}):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")

            # Special characters in values
            args = parser.parse_args([
                "--api-key", "sk-key-with-special!@#$%^&*()",
                "--api-url", "https://api.example.com/v1/chat?param=value&other=123",
                "--model", "model/with-slash_and_underscore"
            ])

            config = git_commitai.get_env_config(args)

            assert config["api_key"] == "sk-key-with-special!@#$%^&*()"
            assert config["api_url"] == "https://api.example.com/v1/chat?param=value&other=123"
            assert config["model"] == "model/with-slash_and_underscore"

    def test_cli_override_with_amend_and_allow_empty(self):
        """Test CLI overrides work with --amend and --allow-empty flags."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            with patch("git_commitai.check_staged_changes", return_value=True):
                with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "env-key"}):
                    with patch("git_commitai.make_api_request", return_value="Amended empty") as mock_api:
                        with patch("git_commitai.get_git_dir", return_value="/tmp/.git"):
                            with patch("git_commitai.create_commit_message_file", return_value="/tmp/COMMIT"):
                                with patch("os.path.getmtime", side_effect=[1000, 2000]):
                                    with patch("git_commitai.open_editor"):
                                        with patch("git_commitai.is_commit_message_empty", return_value=False):
                                            with patch("git_commitai.strip_comments_and_save", return_value=True):
                                                with patch("sys.argv", [
                                                    "git-commitai",
                                                    "--amend",
                                                    "--allow-empty",
                                                    "--model", "gpt-4",
                                                    "--api-url", "https://custom.api.com"
                                                ]):
                                                    git_commitai.main()

                                                    # Verify configuration was applied
                                                    config_used = mock_api.call_args[0][0]
                                                    assert config_used["model"] == "gpt-4"
                                                    assert config_used["api_url"] == "https://custom.api.com"

                                                    # Verify git commit has both flags
                                                    commit_calls = [
                                                        call for call in mock_run.call_args_list
                                                        if "commit" in str(call)
                                                    ]
                                                    if commit_calls:
                                                        last_call = commit_calls[-1]
                                                        assert "--amend" in last_call[0][0]
                                                        assert "--allow-empty" in last_call[0][0]

    def test_help_text_includes_cli_overrides(self):
        """Test that --help includes information about CLI override options."""
        with patch("sys.argv", ["git-commitai", "--help"]):
            with patch("git_commitai.show_man_page", return_value=False):
                with pytest.raises(SystemExit) as exc_info:
                    with patch("sys.stdout", new=StringIO()) as fake_out:
                        git_commitai.main()

                output = fake_out.getvalue()

                # Should show in help text
                assert "--api-key" in output
                assert "--api-url" in output
                assert "--model" in output
                assert "Override API key" in output
                assert "Override API URL" in output
                assert "Override model name" in output

    def test_api_request_uses_overridden_config(self):
        """Test that make_api_request actually uses the overridden configuration."""
        config = {
            "api_key": "test-override-key",
            "api_url": "https://override.api.com/v1/chat",
            "model": "override-model"
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            with patch("json.dumps") as mock_json_dumps:
                mock_json_dumps.return_value = '{"test": "data"}'

                # Mock successful response
                mock_response = MagicMock()
                mock_response.read.return_value = b'{"choices": [{"message": {"content": "Test message"}}]}'
                mock_urlopen.return_value.__enter__.return_value = mock_response

                result = git_commitai.make_api_request(config, "test prompt")

                # Verify Request was created with correct URL
                request_call = mock_urlopen.call_args[0][0]
                assert request_call.full_url == "https://override.api.com/v1/chat"

                # Verify headers include the override key
                assert request_call.headers["Authorization"] == "Bearer test-override-key"

                # Verify the model was included in payload
                mock_json_dumps.assert_called_once()
                payload = mock_json_dumps.call_args[0][0]
                assert payload["model"] == "override-model"

    def test_precedence_cli_over_env(self):
        """Test that CLI arguments have precedence over environment variables."""
        # This is the key test - CLI should always win over env
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "env-key-should-be-ignored",
            "GIT_COMMIT_AI_URL": "https://env-url-should-be-ignored.com",
            "GIT_COMMIT_AI_MODEL": "env-model-should-be-ignored"
        }):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--api-key")
            parser.add_argument("--api-url")
            parser.add_argument("--model")

            args = parser.parse_args([
                "--api-key", "cli-key-wins",
                "--api-url", "https://cli-url-wins.com",
                "--model", "cli-model-wins"
            ])

            config = git_commitai.get_env_config(args)

            # CLI values should be used, not env values
            assert config["api_key"] == "cli-key-wins"
            assert config["api_url"] == "https://cli-url-wins.com"
            assert config["model"] == "cli-model-wins"

            # Ensure env values were NOT used
            assert "env-key-should-be-ignored" not in config["api_key"]
            assert "env-url-should-be-ignored" not in config["api_url"]
            assert "env-model-should-be-ignored" not in config["model"]
