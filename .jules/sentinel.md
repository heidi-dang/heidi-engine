# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Outdated OpenAI Secret Patterns
**Vulnerability:** OpenAI secret patterns were missing hyphen support, failing to detect modern `sk-proj-` key formats. This led to secrets being logged in telemetry and bypassing the validation cleaning gate.
**Learning:** Provider token formats evolve; a restrictive character class like `[a-zA-Z0-9]` can lead to silent security bypasses when new delimiters (like hyphens) are introduced.
**Prevention:** Regularly audit secret detection patterns against current provider formats. Maintain strict consistency between telemetry redaction patterns and dataset validation filters.
