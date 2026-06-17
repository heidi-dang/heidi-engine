## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelization of Subprocess-heavy Pipeline Stages]
**Learning:** Pipeline stages that rely on external subprocesses (like `scripts/03_unit_test_gate.py`) are heavily I/O bound. Parallelizing these with `ThreadPoolExecutor` provides near-linear speedup (~3.4x with 4 workers). Combined regex objects for security scanning also provide a ~5.8x speedup for safe paths.
**Action:** Prioritize parallelization for any stage executing external commands. Use pre-compiled combined regex for high-frequency scanning of safety patterns.
