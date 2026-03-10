# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-05-15 - Path Traversal in Telemetry Run Directory Resolution
**Vulnerability:** The `get_run_dir` function in `heidi_engine/telemetry.py` used direct string concatenation of `run_id`, allowing an attacker to use `..` sequences to access files outside the `runs/` directory (e.g., `/etc/passwd`).
**Learning:** Even internal helper functions used for path construction must sanitize inputs if those inputs can be influenced by environment variables or external calls. Relying on `Path() / run_id` is unsafe if `run_id` contains traversal sequences.
**Prevention:** Always sanitize filename/directory components using `Path(component).name` or equivalent to ensure they remain within the intended parent directory.
