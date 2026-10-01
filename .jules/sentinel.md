# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-10-01 - Path Traversal via Unsanitized Run IDs
**Vulnerability:** Run ID inputs (`RUN_ID` env var or `run_id` parameters) were used directly in `Path` constructions like `Path(AUTOTRAIN_DIR) / "runs" / run_id`, allowing path traversal sequences.
**Learning:** File path constructors using user or environment input must always sanitize directory traversal characters rather than trusting `run_id` format.
**Prevention:** Use `sanitize_run_id()` to strip path separators and non-alphanumeric characters (keeping only `[a-zA-Z0-9_\-]`) before performing file system path joins.
