import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
import git_commitai

class TestAPIRequestRetryMechanism:
    """Test API request retry mechanism in detail."""

    def test_api_request_partial_success(self):
        """Test API request that fails then succeeds."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        # Save original settings
        original_settings = (git_commitai.MAX_RETRIES, git_commitai.RETRY_DELAY, git_commitai.RETRY_BACKOFF)
        git_commitai.MAX_RETRIES = 3
        git_commitai.RETRY_DELAY = 0
        git_commitai.RETRY_BACKOFF = 1

        call_count = [0]

        def urlopen_side_effect(req, timeout=None):
            call_count[0] += 1
            if call_count[0] < 3:
                raise URLError("Connection failed")

            # Success on third attempt
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"choices": [{"message": {"content": "Success"}}]}'
            mock_response.__enter__ = lambda self: self
            mock_response.__exit__ = lambda self, *args: None
            return mock_response

        with patch("git_commitai.urlopen", side_effect=urlopen_side_effect):
            result = git_commitai.make_api_request(config, "test")
            assert result == "Success"
            assert call_count[0] == 3

        # Restore original settings
        git_commitai.MAX_RETRIES, git_commitai.RETRY_DELAY, git_commitai.RETRY_BACKOFF = original_settings

    def test_api_request_backoff_timing(self):
        """Test that retry backoff works correctly."""
        config = {
            "api_key": "test-key",
            "api_url": "https://api.example.com",
            "model": "test-model",
        }

        original_settings = (git_commitai.MAX_RETRIES, git_commitai.RETRY_DELAY, git_commitai.RETRY_BACKOFF)
        git_commitai.MAX_RETRIES = 2
        git_commitai.RETRY_DELAY = 0.1
        git_commitai.RETRY_BACKOFF = 2

        with patch("git_commitai.urlopen", side_effect=URLError("Failed")):
            with patch("git_commitai.time.sleep") as mock_sleep:
                with pytest.raises(SystemExit):
                    git_commitai.make_api_request(config, "test")

                # Check backoff delays
                assert mock_sleep.call_count == 1  # Only one retry (2 total attempts)
                mock_sleep.assert_called_with(0.1)  # First retry delay

        # Restore original settings
        git_commitai.MAX_RETRIES, git_commitai.RETRY_DELAY, git_commitai.RETRY_BACKOFF = original_settings
