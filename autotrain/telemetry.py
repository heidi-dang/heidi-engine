"""Telemetry module for Heidi Engine.

Provides secret redaction and event logging for the autotraining pipeline.
"""

import re
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


SECRET_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN]"),
    (r"github_pat_[a-zA-Z0-9_]{22,}", "[GITHUB_TOKEN]"),
    (r"sk-[a-zA-Z0-9]{20,}", "[OPENAI_KEY]"),
    (r"glpat-[a-zA-Z0-9\-]{20,}", "[GITLAB_TOKEN]"),
    (r"AKIA[0-9A-Z]{16}", "[AWS_KEY]"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "[PRIVATE_KEY]"),
    (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "[SSH_KEY]"),
    (r"(?i)bearer\s+[a-zA-Z0-9\-_\.]{20,}", "[BEARER_TOKEN]"),
    (r"(?i)(api[_-]?key|secret)[_\-]?['\"]?\s*[:=]\s*['\"]?[\w\-]{20,}", "[ENV_SECRET]"),
    (r"(?i)password\s*[:=]\s*[\"'][^\"']{8,}[\"']", "[PASSWORD]"),
]

ALLOWED_EVENT_FIELDS = {
    "event_version", "ts", "run_id", "round", "stage",
    "level", "event_type", "message", "counters", "usage", "model"
}

ALLOWED_STATUS_FIELDS = {
    "run_id", "status", "stage", "round", "counters", "usage", "ts"
}


def redact_secrets(text: Any) -> str:
    """Redact secrets from text."""
    if text is None:
        return "None"
    
    text = str(text)
    
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def sanitize_for_log(data: Any, max_length: int = 1000) -> str:
    """Sanitize data for logging."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            sanitized[k] = sanitize_for_log(v, max_length)
        return str(sanitized)
    elif isinstance(data, list):
        return str([sanitize_for_log(item, max_length) for item in data])
    elif isinstance(data, str):
        redacted = redact_secrets(data)
        if len(redacted) > max_length:
            return redacted[:max_length] + "..."
        return redacted
    else:
        return redact_secrets(data)


def emit_event(
    event_type: str,
    message: str,
    stage: str = "",
    round_num: int = 0,
    counters_delta: Optional[Dict] = None,
    usage_delta: Optional[Dict] = None,
    model: str = ""
):
    """Emit a telemetry event."""
    event = {
        "event_version": "1.0",
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": "",
        "round": round_num,
        "stage": stage,
        "level": "info",
        "event_type": event_type,
        "message": message,
    }
    if counters_delta:
        event["counters"] = counters_delta
    if usage_delta:
        event["usage"] = usage_delta
    if model:
        event["model"] = model
    
    print(sanitize_for_log(json.dumps(event)), file=sys.stderr)


def flush_events():
    """Flush events (no-op for stderr-based logging)."""
    pass


def main():
    """CLI entry point for telemetry."""
    print("Heidi Telemetry v0.1.0")


if __name__ == "__main__":
    main()
