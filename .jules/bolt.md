## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2024-06-28 - [Parallelized Unit Testing and Regex Optimization]
**Learning:** Sequential subprocess execution in  was a major pipeline bottleneck. Parallelizing with  (4 workers) yielded a ~2.7x wall-clock speedup for 100 samples. Pre-compiling regex and using  for code extraction further optimized the hot path.
**Action:** Always parallelize I/O-bound tasks involving subprocesses and pre-compile regex patterns used in loops. Use `textwrap.indent` for safe code injection into templates to avoid indentation errors.

## 2024-06-28 - [Parallelized Unit Testing and Regex Optimization]
**Learning:** Sequential subprocess execution in `03_unit_test_gate.py` was a major pipeline bottleneck. Parallelizing with `ThreadPoolExecutor` (4 workers) yielded a ~2.7x wall-clock speedup for 100 samples. Pre-compiling regex and using `finditer` for code extraction further optimized the hot path.
**Action:** Always parallelize I/O-bound tasks involving subprocesses and pre-compile regex patterns used in loops. Use `textwrap.indent` for safe code injection into templates to avoid indentation errors.
