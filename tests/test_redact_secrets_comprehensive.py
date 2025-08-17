import git_commitai

class TestRedactSecretsComprehensive:
    """Comprehensive tests for redact_secrets function."""

    def test_redact_short_api_key(self):
        """Test that short API keys are handled."""
        # Short keys might not match the 32+ character pattern
        # Let's use a pattern that will match
        message = "api_key=short123"  # This should match the api_key pattern
        result = git_commitai.redact_secrets(message)
        assert "=[REDACTED]" in result

    def test_redact_callable_replacement(self):
        """Test redaction with callable replacement functions."""
        # Test with a very long API key to trigger the lambda function
        message = "API: abcdefghijklmnopqrstuvwxyz123456789ABCDEFGHIJKLMNOP"
        result = git_commitai.redact_secrets(message)
        # Should show first 4 and last 4 characters
        assert "abcd...MNOP" in result

    def test_redact_mixed_sensitive_data(self):
        """Test redacting multiple types of sensitive data in one message."""
        message = """
        API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz
        Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
        Basic dXNlcjpwYXNz
        oauth_token=abc123
        {"apiKey": "secret", "token": "mytoken"}
        https://user:pass@example.com
        ssh-rsa AAAAB3NzaC1yc2EAAAADAQAB
        """

        result = git_commitai.redact_secrets(message)

        # Check all types are redacted
        assert "sk-1234567890abcdefghijklmnopqrstuvwxyz" not in result
        assert "Bearer [REDACTED]" in result
        assert "Basic [REDACTED]" in result
        assert "oauth_token=[REDACTED]" in result
        assert '"apiKey"=[REDACTED]' in result or '"apiKey": "[REDACTED]"' in result
        assert '"token": "[REDACTED]"' in result
        assert "[USER]:[PASS]@" in result
        assert "ssh-rsa AAAA...[REDACTED]" in result or "ssh-rsa AAAAB3NzaC...[REDACTED]" in result
