## 2026-02-19 - [Command Injection in Orchestration Scripts]
**Vulnerability:** Shell variables were directly interpolated into `python3 -c` code strings in `scripts/loop.sh` and `scripts/common.sh`.
**Learning:** This is a classic command injection vector. Any single quote in a variable like `$message` could break the Python string literal and execute arbitrary code.
**Prevention:** Always pass shell variables via `sys.argv` and use `json.loads` for complex data structures instead of string interpolation.

## 2026-02-19 - [Subshell Capture Pollution]
**Vulnerability:** Captured output from functions like `run_teacher_generate` included log messages from `log_step` and synthetic prints from tools, causing downstream file path failures.
**Learning:** Using `$(...)` captures everything on `stdout`. If a function is intended to return a value (like a path), all other outputs must be redirected to `stderr`.
**Prevention:** Redirect all non-return output in bash functions to `>&2`.
