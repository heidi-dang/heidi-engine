# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2026-03-17 - Path Traversal in Telemetry Run Directory
**Vulnerability:** The `get_run_dir` function in both `telemetry.py` and `dashboard.py` was vulnerable to path traversal, allowing an attacker to read or write files outside the intended `runs/` directory by manipulating the `run_id`.
**Learning:** Using untrusted user input directly in `pathlib.Path` constructions without sanitization can lead to serious security risks, even if the application is intended for local use.
**Prevention:** Always sanitize identifiers or filenames provided by users by using `Path(input).name` to extract only the final component of the path, effectively blocking traversal sequences like `../`.
