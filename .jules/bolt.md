## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-19 - [Parallelized Unit Test Gate]
**Learning:** Subprocess execution in unit test gates is a massive sequential bottleneck. Parallelizing with ThreadPoolExecutor (capped at 8 workers) provides a ~3x-5x speedup for I/O bound test execution. Also discovered that injected code in f-string templates MUST be explicitly indented using textwrap.indent to avoid SyntaxErrors in the child process.
**Action:** Always parallelize subprocess-heavy pipeline stages and use textwrap.indent for dynamic code injection.
