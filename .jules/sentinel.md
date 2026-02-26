# Sentinel Security Journal

## 2024-05-22 - Path Traversal in Telemetry Run ID
**Vulnerability:** The `get_run_dir` function in `heidi_engine/telemetry.py` used the `run_id` directly to construct a file path without sanitization, allowing for arbitrary directory creation and potential file hijacking via malicious `run_id` values (e.g., `../../etc`).
**Learning:** Using `Path(run_id)` or string concatenation with user-provided identifiers can lead to path traversal if the identifier contains relative (`..`) or absolute (`/`) path components.
**Prevention:** Always sanitize user-provided identifiers by using `Path(id).name` to extract only the filename component and provide a safe fallback for empty or reserved names (like `.` or `..`). Implement defense-in-depth by verifying that resolved paths remain within the intended parent directory.
