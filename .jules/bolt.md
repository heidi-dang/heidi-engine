## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2025-05-15 - [Parallelizing Subprocess Execution and Regex Optimizations]
**Learning:** Parallelizing I/O-bound tasks like subprocess execution using `ThreadPoolExecutor` provides massive speedups (e.g., ~5x for unit tests). Additionally, replacing sequential `any(kw in text for kw in keywords)` loops or multiple `re.search` calls with a single pre-compiled combined regex search can yield significant performance gains (2x-5x) for high-frequency string processing.
**Action:** Use `ThreadPoolExecutor` for parallelizing I/O-bound subprocesses. Combine multiple string/regex checks into a single-pass regex search for critical paths. Use `.replace()` instead of f-strings when injecting untrusted code to avoid curly brace interpolation issues.
