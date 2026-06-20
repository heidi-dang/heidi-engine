## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallel Unit Test Gate and Regex Optimization]
**Learning:** Parallelizing subprocess-heavy tasks like unit test execution using `ThreadPoolExecutor` (8 workers) provided a ~2.4x speedup for 100 samples. Heuristic keyword checks are ~2.6x faster when using a single pre-compiled regex compared to an `any()` loop over a list of keywords.
**Action:** Always consider parallelization for I/O or subprocess-bound tasks. Use pre-compiled regex for frequent string heuristic checks. Always use `textwrap.indent` when injecting code into templates to maintain valid syntax.
