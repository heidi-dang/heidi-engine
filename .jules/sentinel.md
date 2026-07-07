# Sentinel Security Journal

## 2025-01-24 - Missing Authentication on Telemetry Endpoints
**Vulnerability:** Telemetry HTTP endpoints (`/status`, `/`) were completely unprotected, allowing any local user to view training state, usage, and costs.
**Learning:** Initial implementation prioritized ease of use and local-only binding (`127.0.0.1`) but neglected defense-in-depth requirements for multi-user or shared environments.
**Prevention:** Always implement at least Basic Authentication for any endpoint exposing state or metadata, even if restricted to loopback. Use random session-specific credentials if no configuration is provided.

## 2025-01-24 - Brittle Security Sandbox Execution
**Vulnerability:** The unit test gate in `scripts/03_unit_test_gate.py` was effectively disabled because it attempted to execute generated Python code within a `try` block without proper indentation, causing a `SyntaxError` and triggering a fallback that masked the failure.
**Learning:** Dynamic code injection into execution wrappers is brittle. Relying on simple string formatting for code blocks within control structures (like `try/except`) leads to syntax failures that can bypass security checks if not explicitly handled as a fatal error.
**Prevention:** Always use `textwrap.indent` when injecting multi-line code into a block. Ensure that the test wrapper itself is unit-tested for successful execution of valid code.
