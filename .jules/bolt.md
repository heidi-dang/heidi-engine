## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallel Unit Testing and Regex Optimization]
**Learning:** Parallelizing subprocess-heavy tasks like unit testing can yield significant speedups (~2.4x on 4 cores) even with Python's GIL. Additionally, using `textwrap.indent` is essential when dynamically wrapping code blocks in `try...except` blocks to prevent `SyntaxError`.
**Action:** Use `ThreadPoolExecutor` for IO-bound or subprocess-heavy pipeline stages. Always pre-compile regex patterns and use `textwrap.indent` for robust code generation/wrapping.
