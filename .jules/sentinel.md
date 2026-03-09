# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Insufficient Sanitization with os.path.basename
**Vulnerability:** Path traversal via `run_id` in telemetry and dashboard modules.
**Learning:** Using `os.path.basename()` alone is insufficient to prevent all path traversal. While it strips directory components, it returns `".."` if the input is `".."`, allowing a climb to the parent directory (e.g., `runs/..`).
**Prevention:** Always explicitly check for and reject or sanitize special directory markers (`.`, `..`) after applying `basename()`. Centralize path construction in a single, well-tested module to ensure consistent enforcement across the codebase.
