# Sentinel's Journal - Security Learnings

## 2025-01-24 - Path Traversal in Telemetry Run IDs
**Vulnerability:** Path Traversal in `get_run_dir` and `_rotate_events_log`.
**Learning:** The application trusted the `run_id` provided via environment variables or CLI arguments to construct file system paths. This allowed directory traversal using `..` sequences, which could lead to arbitrary directory creation or unauthorized file rotation/deletion.
**Prevention:** Always sanitize user-provided identifiers that are used in path construction. Using `Path(input).name` is an effective way to extract only the last component and prevent traversal. Additionally, use `.resolve()` and verify that the final path is a child of the expected root directory as a defense-in-depth measure.
