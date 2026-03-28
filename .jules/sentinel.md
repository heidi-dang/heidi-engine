# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run IDs
**Vulnerability:** The `run_id` was used directly in path construction without sanitization, allowing attackers to write or read files outside the intended `runs/` directory using traversal sequences like `../../`.
**Learning:** External inputs (env vars or function args) used for file paths must always be treated as untrusted and sanitized. Even internal-looking IDs can be manipulated in multi-user environments.
**Prevention:** Always use `os.path.basename()` on user-provided strings before using them in path construction. Provide safe, unique fallbacks for invalid or dangerous inputs (e.g., `.`, `..`, or empty strings).
