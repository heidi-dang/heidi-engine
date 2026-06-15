## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-06-15 - [Parallelizing Unit Test Gate]
**Learning:** Subprocess-heavy validation steps like `03_unit_test_gate.py` are major sequential bottlenecks. Parallelizing with `ThreadPoolExecutor` (capped at 8 workers) provided a ~5.5x speedup for 20 samples.
**Action:** Identify pipeline stages involving independent subprocess execution or API calls and prioritize parallelization over micro-optimizations.

## 2026-06-15 - [Redundant Cache Logic]
**Learning:** Over-complicating cache checks (e.g., secondary checks with different arguments) can introduce bugs like `NameError` and `TypeError` if not thoroughly tested, negating the performance benefits.
**Action:** Keep thread-safe cache logic simple and centralized at the function entry point.
