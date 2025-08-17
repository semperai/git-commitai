"""Tests for API request handling."""

import pytest
import json
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

import git_commitai

# Override retry configuration for faster tests
git_commitai.MAX_RETRIES = 1
git_commitai.RETRY_DELAY = 0
git_commitai.RETRY_BACKOFF = 1


class TestAPIRequest:
    """Test API request handling."""

    def test_successful_api_request(self):
        """Test successful API request."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        mock_response = {
            "choices": [{"message": {"content": "Fix bug in authentication"}}]
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                json.dumps(mock_response).encode()
            )

            result = git_commitai.make_api_request(config, "test message")
            assert result == "Fix bug in authentication"

    def test_api_request_error(self):
        """Test API request error handling."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", {}, None)

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")

    def test_api_response_parse_error(self):
        """Test handling of malformed API responses."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        with patch("git_commitai.urlopen") as mock_urlopen:
            # Return invalid JSON
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b"invalid json"

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")

    def test_api_response_missing_fields(self):
        """Test handling of API response with missing fields."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        mock_response = {"choices": []}  # Missing message content

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = (
                json.dumps(mock_response).encode()
            )

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")


class TestEnvConfig:
    """Test environment configuration handling."""

    def test_no_api_key(self):
        """Test behavior when API key is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(SystemExit):
                # Create a mock args object with no overrides
                mock_args = MagicMock()
                mock_args.api_key = None
                mock_args.api_url = None
                mock_args.model = None
                git_commitai.get_env_config(mock_args)

    def test_with_api_key(self):
        """Test configuration with API key set."""
        with patch.dict("os.environ", {"GIT_COMMIT_AI_KEY": "test-key"}):
            # Create a mock args object with no overrides
            mock_args = MagicMock()
            mock_args.api_key = None
            mock_args.api_url = None
            mock_args.model = None

            config = git_commitai.get_env_config(mock_args)
            assert config["api_key"] == "test-key"
            assert config["api_url"] == "https://openrouter.ai/api/v1/chat/completions"  # default
            assert config["model"] == "qwen/qwen3-coder"  # default

    def test_with_custom_config(self):
        """Test configuration with custom values."""
        with patch.dict("os.environ", {
            "GIT_COMMIT_AI_KEY": "custom-key",
            "GIT_COMMIT_AI_URL": "https://custom-api.com",
            "GIT_COMMIT_AI_MODEL": "custom-model"
        }):
            # Create a mock args object with no overrides
            mock_args = MagicMock()
            mock_args.api_key = None
            mock_args.api_url = None
            mock_args.model = None

            config = git_commitai.get_env_config(mock_args)
            assert config["api_key"] == "custom-key"
            assert config["api_url"] == "https://custom-api.com"
            assert config["model"] == "custom-model"
