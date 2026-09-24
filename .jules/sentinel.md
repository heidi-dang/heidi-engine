# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - OpenAI Project Key Format Bypasses Secret Redaction
**Vulnerability:** OpenAI `sk-proj-` keys contain hyphens and passed through secret detection in `scripts/02_validate_clean.py` and redaction in `heidi_engine/telemetry.py`.
**Learning:** Legacy secret regexes like `sk-[a-zA-Z0-9]{48,}` fail on modern key formats that use prefixes and hyphens (`sk-proj-...`).
**Prevention:** Use flexible regexes allowing hyphens and variable lengths (`sk-[a-zA-Z0-9\-]{20,}`) for token formats that evolve over time.
