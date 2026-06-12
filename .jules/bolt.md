## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelized Unit Test Gate and Regex Optimization]
**Learning:** `ThreadPoolExecutor` is highly effective for parallelizing tasks that involve waiting on subprocesses (like running unit tests). Additionally, combining multiple individual regex patterns into a single pre-compiled pattern provides a measurable ~5-6x speedup for safe code samples by reducing the number of passes over the text.
**Action:** Use `ThreadPoolExecutor` for subprocess-heavy pipelines and prefer combined pre-compiled regexes for single-pass scanning of large datasets.
