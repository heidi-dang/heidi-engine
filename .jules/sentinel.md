# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Path Traversal in Telemetry Run ID
**Vulnerability:** The `run_id` sourced from environment variables or function calls was used directly in file paths without sanitization, allowing path traversal (e.g., `RUN_ID=../../etc/passwd`).
**Learning:** Even internal-facing identifiers must be sanitized when used for file system operations. `os.path.basename` is a simple but effective defense for this pattern.
**Prevention:** Always sanitize user-controllable input before using it to construct file paths. Use `os.path.basename` and validate the resulting name against expected patterns or reserved names.

## 2025-01-24 - Environment Variable Leak in Unit Test Gate
**Vulnerability:** The `subprocess.run` call in the unit test gate passed the entire host environment to executed code, potentially leaking secrets like `OPENAI_API_KEY` to generated code.
**Learning:** Subprocesses should run with the principle of least privilege, including a minimal environment. Indentation of dynamic code blocks must also be handled carefully when wrapping them in a `try...except` block to avoid syntax errors that could bypass security checks.
**Prevention:** Always pass a restricted `env` dictionary to `subprocess.run`. Use `textwrap.indent` to safely embed dynamic code into templates.
