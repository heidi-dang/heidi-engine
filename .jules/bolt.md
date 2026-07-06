## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-07-06 - [Parallelized Unit Test Gate]
**Learning:** Sequential subprocess execution is a major bottleneck in CI/CD pipelines. Parallelizing with `ThreadPoolExecutor` and pre-compiling regex patterns can yield significant speedups (e.g. ~2.7x on 4-core systems) for validation tasks. Using `textwrap.indent` is safer than manual f-string indentation for code generation.
**Action:** Prioritize parallelization for I/O bound or subprocess-heavy tasks. Pre-compile regex at module level. Use robust code wrapping for test execution.
