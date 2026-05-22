# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-25 - Path Traversal in Telemetry Run IDs
**Vulnerability:** The `get_run_dir` function in `heidi_engine/telemetry.py` was vulnerable to path traversal because it directly joined a user-provided `run_id` with a base directory using `pathlib.Path`. An absolute path or `..` components in `run_id` could allow escaping the intended `runs/` directory.
**Learning:** `pathlib.Path`'s join operator (`/`) has a security-relevant behavior: if the second operand is an absolute path, it completely ignores the first operand. Using `os.path.join` or `Path / run_id` without sanitization is unsafe for user-controlled input.
**Prevention:** Always sanitize user-provided identifiers that are used as path components. Use `Path(identifier).name` to extract only the final filename component and prevent navigation outside the intended directory.
