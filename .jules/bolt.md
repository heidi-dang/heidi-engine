## 2026-02-20 - [Optimized Telemetry Redaction and Sanitization]
**Learning:** Sequential `re.sub` calls are faster than combined regex callbacks for small pattern sets, but the biggest performance win comes from early-exit fast-paths (e.g., checking for `\x1b` or secret keywords) and proper ordering of truncation vs. redaction for large strings.
**Action:** Always implement fast-path guards for expensive string processing and ensure that heavy operations (like regex) are performed on the smallest possible data subset (e.g., after truncation).

## 2026-02-21 - [Parallelizing I/O-Bound Subprocess Tasks]
**Learning:** For pipeline stages that involve numerous independent subprocess calls (like unit testing generated code), parallelization using `ThreadPoolExecutor` provides a massive speedup (e.g., ~3x-5x) with minimal code complexity.
**Action:** Identify sequential I/O-bound loops (API calls, subprocesses, disk I/O) and parallelize them using thread pools, while being mindful of resource limits (e.g., capping workers to 8).

## 2026-02-21 - [Regex Performance in Validation Loops]
**Learning:** Combined regex objects (`|`.join(patterns)) are excellent for fast-path "any match" checks, but they must be carefully constructed. Including ubiquitous characters (like quotes in code strings) in a fast-path pattern will negate its performance benefits. Pre-compiling individual patterns for the subsequent "which match" loop is also essential for maximum throughput in tight loops.
**Action:** Use pre-compiled combined regexes for fast-path exits and pre-compiled individual regexes for detail loops. Avoid ubiquitous characters in fast-path indicators.
