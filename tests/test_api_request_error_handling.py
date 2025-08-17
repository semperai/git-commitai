import pytest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import git_commitai

class TestAPIRequestErrorHandling:
    """Test additional API request error scenarios."""

    def test_api_request_client_error_no_retry(self):
        """Test that 4xx errors don't retry."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        # Override retry settings for faster test
        original_max_retries = git_commitai.MAX_RETRIES
        git_commitai.MAX_RETRIES = 3
        git_commitai.RETRY_DELAY = 0

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = HTTPError("url", 401, "Unauthorized", {}, None)

            with pytest.raises(SystemExit) as exc_info:
                git_commitai.make_api_request(config, "test message")

            assert exc_info.value.code == 1
            # Should only call once for 4xx errors (no retries)
            assert mock_urlopen.call_count == 1

        git_commitai.MAX_RETRIES = original_max_retries

    def test_api_request_server_error_with_retry(self):
        """Test that 5xx errors do retry."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        original_max_retries = git_commitai.MAX_RETRIES
        git_commitai.MAX_RETRIES = 2
        git_commitai.RETRY_DELAY = 0

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", {}, None)

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")

            # Should retry for 5xx errors
            assert mock_urlopen.call_count == 2

        git_commitai.MAX_RETRIES = original_max_retries

    def test_api_request_url_error(self):
        """Test handling URLError."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        original_max_retries = git_commitai.MAX_RETRIES
        git_commitai.MAX_RETRIES = 1
        git_commitai.RETRY_DELAY = 0

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = URLError("Connection refused")

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")

        git_commitai.MAX_RETRIES = original_max_retries

    def test_api_request_json_decode_error_retry(self):
        """Test JSON decode error with retry."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        original_max_retries = git_commitai.MAX_RETRIES
        git_commitai.MAX_RETRIES = 2
        git_commitai.RETRY_DELAY = 0

        with patch("git_commitai.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = b"not json"

            with pytest.raises(SystemExit):
                git_commitai.make_api_request(config, "test message")

            assert mock_urlopen.call_count == 2

        git_commitai.MAX_RETRIES = original_max_retries

