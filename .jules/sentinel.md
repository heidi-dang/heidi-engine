# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Environment Variable Leak in Unit Test Gate
**Vulnerability:** The `03_unit_test_gate.py` script executed generated code in a subprocess that inherited the full environment of the runner, potentially exposing sensitive API keys and tokens to untrusted code.
**Learning:** Executing code in a subprocess without explicit environment filtering is a common source of data leakage in LLM-powered pipelines. A secondary functional bug in code wrapping (indentation) also prevented the gate from correctly capturing execution failures.
**Prevention:** Always filter `os.environ` to remove sensitive keys (e.g., matching `KEY`, `TOKEN`, `SECRET`) before passing it to subprocesses. Use `textwrap.indent` to safely nest generated code within execution templates. Expand dangerous pattern lists to include reflection/meta-programming modules like `importlib` and `inspect`.
