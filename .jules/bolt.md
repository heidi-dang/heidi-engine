## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelizing Unit Test Gate]
**Learning:** For IO-bound tasks involving multiple subprocess executions (like unit testing 100+ generated code samples), `ThreadPoolExecutor` provides a massive performance boost (~2.8x speedup) by overlapping waiting times. Combined with module-level pre-compiled regex for extraction, it significantly reduces pipeline duration.
**Action:** Identify sequential loops that execute external commands and parallelize them using a thread pool based on `os.cpu_count()`.
