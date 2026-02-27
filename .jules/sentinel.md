# Sentinel Security Journal

## 2024-05-22 - [CRITICAL] Path Traversal in Telemetry Module
**Vulnerability:** The `get_run_dir` function was directly using the `run_id` to construct file paths, allowing an attacker to escape the `runs/` directory using `..` sequences. Similarly, `_rotate_events_log` did not validate that the rotation target was within the expected directory.
**Learning:** Even internal utility functions that handle identifiers can be entry points for path traversal if those identifiers are sourced from external inputs (like environment variables or API requests). Relying on path concatenation without sanitization or resolution validation is dangerous.
**Prevention:** Always sanitize identifiers using `Path(id).name` to strip directory components. For sensitive file operations like rotation or deletion, validate the resolved absolute path against a trusted base directory using `.resolve()` and parent checking.
