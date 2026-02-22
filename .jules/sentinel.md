## 2025-05-15 - [Path Traversal in Telemetry]
**Vulnerability:** Path traversal in `get_run_dir` and `_rotate_events_log` via unsanitized `run_id` and `events_file` paths.
**Learning:** Even if documentation or memory claims a security feature is present, always verify the actual source code. Path construction using `Path(base) / user_input` is unsafe if `user_input` can contain `..`.
**Prevention:** Use `Path(input).name` to restrict inputs to a single filename component, and use `base_dir.resolve() in resolved_path.parents` for robust path validation before performing file operations.
