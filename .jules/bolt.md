## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-23 - [Parallelized Unit Test Gate]
**Learning:** Sequential subprocess execution in the unit test gate was a major bottleneck. Parallelizing with `ThreadPoolExecutor` provided a ~3x speedup on 4-core systems. Also, injecting user code into a `try` block requires explicit indentation (`textwrap.indent`) to avoid `IndentationError`.
**Action:** Use parallelism for independent I/O-bound tasks like subprocess execution. Always ensure proper indentation when generating or injecting Python code.
