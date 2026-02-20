## 2024-05-24 - Telemetry Path Traversal and Secret Leakage
**Vulnerability:** Path traversal via `run_id` in `get_run_dir` and information leakage of secrets in dictionary keys in `sanitize_for_log`.
**Learning:** `Path.joinpath` (or `/` operator) in Python's `pathlib` ignores all previous path components if an absolute path is provided as an argument. Additionally, recursive sanitization of dictionaries must include keys, as secrets can sometimes be placed there.
**Prevention:** Always use `Path(input).name` to sanitize user-provided path components. When redacting secrets from structured data, ensure both keys and values are processed.
