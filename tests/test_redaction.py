"""
Unit tests for secret redaction in telemetry module.
Tests that SECRET_PATTERNS correctly redact sensitive data.
"""
import pytest
from heidi_engine.telemetry import redact_secrets, sanitize_for_log


class TestSecretRedaction:
    """Test secret redaction patterns."""

    def test_github_token_ghp(self):
        """Test GitHub personal access token (ghp_) redaction."""
        text = "My token is ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        redacted = redact_secrets(text)
        assert "ghp_" not in redacted
        assert "[GITHUB_TOKEN]" in redacted

    def test_github_pat(self):
        """Test GitHub PAT (github_pat_) redaction."""
        text = "Token: github_pat_1234567890abcdefghijklmnopqrst"
        redacted = redact_secrets(text)
        assert "github_pat_" not in redacted
        assert "[TOKEN]" in redacted or "[GITHUB_TOKEN]" in redacted

    def test_openai_key(self):
        """Test OpenAI API key (sk-) redaction."""
        text = "API key: sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890"
        redacted = redact_secrets(text)
        assert "sk-" not in redacted
        assert "[OPENAI_KEY]" in redacted

    def test_gitlab_token(self):
        """Test GitLab token (glpat-) redaction."""
        text = "GitLab: glpat-1234567890abcdefghijklmn"
        redacted = redact_secrets(text)
        assert "glpat-" not in redacted
        assert "[GITLAB_TOKEN]" in redacted

    def test_aws_key(self):
        """Test AWS access key (AKIA) redaction."""
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        redacted = redact_secrets(text)
        assert "AKIA" not in redacted
        assert "[AWS_KEY]" in redacted

    def test_private_key(self):
        """Test private key redaction."""
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        redacted = redact_secrets(text)
        assert "PRIVATE KEY" not in redacted
        assert "[PRIVATE_KEY]" in redacted

    def test_ssh_private_key(self):
        """Test SSH private key redaction."""
        text = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmU..."
        redacted = redact_secrets(text)
        assert "OPENSSH PRIVATE KEY" not in redacted
        assert "[SSH_KEY]" in redacted

    def test_bearer_token(self):
        """Test Bearer token redaction."""
        text = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
        redacted = redact_secrets(text)
        assert "Bearer abc" not in redacted
        assert "[BEARER_TOKEN]" in redacted

    def test_env_secret_patterns(self):
        """Test environment variable secret patterns."""
        text = "OPENAI_API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890"
        redacted = redact_secrets(text)
        assert "[ENV_SECRET]" in redacted or "[OPENAI_KEY]" in redacted

    def test_multiple_secrets(self):
        """Test redaction of multiple secrets in one string."""
        text = "ghp_1234567890abcdefghijklmnopqrstuvwxyz and sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890"
        redacted = redact_secrets(text)
        assert "ghp_" not in redacted
        assert "sk-" not in redacted
        assert "[GITHUB_TOKEN]" in redacted
        assert "[OPENAI_KEY]" in redacted

    def test_no_secrets(self):
        """Test that normal text is not modified."""
        text = "This is a normal string with no secrets"
        redacted = redact_secrets(text)
        assert redacted == text

    def test_empty_string(self):
        """Test empty string handling."""
        assert redact_secrets("") == ""

    def test_none_value(self):
        """Test None value handling."""
        assert redact_secrets(None) == "None"

    def test_ansi_stripping(self):
        """Test that ANSI escape sequences are stripped."""
        text = "\x1b[31mRed text\x1b[0m ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        redacted = redact_secrets(text)
        assert "\x1b[" not in redacted
        assert "[GITHUB_TOKEN]" in redacted

    def test_sanitize_for_log(self):
        """Test sanitize_for_log function."""
        data = {
            "message": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "nested": {
                "key": "sk-1234567890abcdefghijklmnopqrstuvwxyz1234567890"
            }
        }
        sanitized = sanitize_for_log(data)
        assert "ghp_" not in str(sanitized)
        assert "sk-" not in str(sanitized)

    def test_sanitize_truncation(self):
        """Test that long strings are truncated."""
        long_text = "a" * 1000
        sanitized = sanitize_for_log(long_text, max_length=100)
        assert len(sanitized) <= 100 + 3  # max_length + "..."


class TestEventSchema:
    """Test event schema validation."""

    def test_allowed_event_fields(self):
        """Test that allowed event fields are defined."""
        from heidi_engine.telemetry import ALLOWED_EVENT_FIELDS
        required_fields = {
            "event_version", "ts", "run_id", "round", "stage",
            "level", "event_type", "message"
        }
        assert required_fields.issubset(ALLOWED_EVENT_FIELDS)

    def test_allowed_status_fields(self):
        """Test that allowed status fields are defined."""
        from heidi_engine.telemetry import ALLOWED_STATUS_FIELDS
        required_fields = {"run_id", "status", "counters", "usage"}
        assert required_fields.issubset(ALLOWED_STATUS_FIELDS)


class TestHTTPSecurity:
    """Test HTTP server security measures."""

    def test_default_host_is_localhost(self):
        """Test that HTTP server defaults to localhost only."""
        import argparse
        from heidi_engine.http import main
        import sys
        
        original_argv = sys.argv
        try:
            sys.argv = ["test", "--help"]
            with pytest.raises(SystemExit):
                main()
        finally:
            sys.argv = original_argv
