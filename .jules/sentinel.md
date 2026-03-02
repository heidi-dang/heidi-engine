## 2024-05-24 - [Path Traversal in Telemetry]
**Vulnerability:** User-provided or environment-derived `run_id` was directly used in path construction in `get_run_dir`, allowing potential path traversal.
**Learning:** `Path(run_id)` concatenation is unsafe if `run_id` can be manipulated to include `..` or absolute paths.
**Prevention:** Always use `Path(run_id).name` to extract only the filename component and explicitly block '.', '..', and empty strings, falling back to a safe default.
