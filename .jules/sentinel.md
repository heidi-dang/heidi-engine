# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-02-15 - Unsanitized `run_id` Path Traversal in Telemetry
**Vulnerability:** `get_run_dir` built paths via `Path(AUTOTRAIN_DIR) / "runs" / run_id` without sanitizing `run_id`, allowing path traversal via payloads like `../../../etc/passwd`.
**Learning:** `pathlib.Path` path concatenation (`/`) does not prevent path traversal when given inputs with `..` sequences.
**Prevention:** Always sanitize identifier parameters used in file paths using regex character whitelisting (e.g., `re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)`).
