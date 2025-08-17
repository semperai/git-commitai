from unittest.mock import patch
from io import StringIO

import git_commitai

class TestDebugLog:
    """Test debug logging functionality."""

    def test_debug_log_enabled(self):
        """Test debug logging when enabled."""
        original_debug = git_commitai.DEBUG
        git_commitai.DEBUG = True
        with patch("sys.stderr", new=StringIO()) as fake_err:
            git_commitai.debug_log("Test message")
            output = fake_err.getvalue()
            assert "DEBUG: Test message" in output
        git_commitai.DEBUG = original_debug

    def test_debug_log_disabled(self):
        """Test debug logging when disabled."""
        original_debug = git_commitai.DEBUG
        git_commitai.DEBUG = False
        with patch("sys.stderr", new=StringIO()) as fake_err:
            git_commitai.debug_log("Test message")
            output = fake_err.getvalue()
            assert output == ""
        git_commitai.DEBUG = original_debug

    def test_debug_log_redacts_secrets(self):
        """Test that debug_log redacts sensitive information."""
        original_debug = git_commitai.DEBUG
        git_commitai.DEBUG = True
        with patch("sys.stderr", new=StringIO()) as fake_err:
            # The API key is being redacted - it shows first 4 and last 4 chars
            git_commitai.debug_log("API key is sk-1234567890abcdefghijklmnopqrstuvwxyz")
            output = fake_err.getvalue()

            # The key IS being redacted to show first 4 and last 4 chars
            assert "sk-1234567890abcdefghijklmnopqrstuvwxyz" not in output
            assert "sk-1234...wxyz" in output or "sk-12...wxyz" in output
        git_commitai.DEBUG = original_debug

