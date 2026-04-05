# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Host Secret Leakage to Untrusted Test Code
**Vulnerability:** The unit test gate executed generated (untrusted) code using `subprocess.run` with the full host environment, allowing code to access sensitive host secrets like `OPENAI_API_KEY`.
**Learning:** Even internal validation steps must be treated as untrusted if they execute dynamically generated content. Standard `os.environ` can contain highly sensitive keys in development or CI environments.
**Prevention:** Always filter the environment passed to subprocesses when executing untrusted code. Blacklist common secret-related keywords (KEY, TOKEN, SECRET, PASS) from the environment.
