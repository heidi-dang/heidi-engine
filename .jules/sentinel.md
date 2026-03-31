# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Path Traversal in Telemetry Run IDs
**Vulnerability:** Run IDs from environment variables and function arguments were used directly to construct file paths, allowing an attacker to write or read files outside the intended `runs/` directory (e.g., `RUN_ID=../../etc`).
**Learning:** Even internal-looking identifiers like `run_id` must be treated as untrusted input if they can be influenced by environment variables or API calls.
**Prevention:** Always use `os.path.basename()` to sanitize file-system identifiers. Implement a safe fallback (like a UUID) for malicious inputs like `..` or empty strings.
