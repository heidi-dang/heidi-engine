# Sentinel's Journal

## 2024-11-20 - [Path Traversal in Telemetry]
**Vulnerability:** The `get_run_dir` function in `heidi_engine/telemetry.py` used unsanitized `run_id` to construct file paths, allowing for path traversal.
**Learning:** Using `Path(AUTOTRAIN_DIR) / "runs" / run_id` is unsafe if `run_id` can be controlled by a user and contains `..`.
**Prevention:** Always sanitize user-provided identifiers using `Path(run_id).name` or equivalent to ensure they stay within the intended directory.
